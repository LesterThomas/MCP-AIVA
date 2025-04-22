import logging
import sys
from pathlib import Path

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "aiva-mcp-server.log"),
        logging.StreamHandler(sys.stderr),
    ],
)

logger = logging.getLogger("aiva-mcp")

logger.info("AIVA MCP Server")

# ---------------------------------------------------------------------------------------------
# AIVA API Calling


import json
import httpx
from httpx import Timeout, TransportError
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# Path to the JSON service-account key file
SERVICE_ACCOUNT_FILE = "C:\\Dev\\lesterthomas\\MCP-AIVA\\vodafone-key.json"

# Reasoning Engine endpoint URL
API_URL = "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/982845833565/locations/us-central1/reasoningEngines/156728785469702144:query"


def get_access_token():

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())
    return credentials.token


def find_key_recursively(data, target_key):
    """Recursively search for a key in a nested dictionary or list."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                yield value
            else:
                yield from find_key_recursively(value, target_key)
    elif isinstance(data, list):
        for item in data:
            yield from find_key_recursively(item, target_key)


async def call_reasoning_agent(query: str):
    """Make an async request to the reasoning agent.

    Args:
        query: The query string to send to the reasoning agent

    Returns:
        JSON response from the agent if successful, None otherwise

    Raises:
        Various httpx exceptions are caught and logged
    """
    try:
        token = get_access_token()
    except Exception as e:
        logger.error(f"Failed to get access token: {e}")
        return None

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"input": {"input": query}}

    # Configure longer timeouts (in seconds)
    timeout = Timeout(
        connect=10.0,  # connection timeout
        read=30.0,  # read timeout
        write=10.0,  # write timeout
        pool=5.0,  # pool timeout
    )

    # Configure client with timeout and limits
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        ) as client:
            try:
                response = await client.post(API_URL, headers=headers, json=payload)
                response.raise_for_status()

                if response.status_code == 200:
                    try:
                        response_json = response.json()
                        logger.info("✅ Response received successfully")

                        # Save response to file with error handling
                        try:
                            with open("response.json", "w") as f:
                                json.dump(response_json, f, indent=2)
                        except IOError as e:
                            logger.error(f"Failed to save response to file: {e}")

                        logger.info("=================================================")
                        logger.info("Output")
                        output = response_json.get("output", {}).get("output")
                        if output:
                            logger.info(output)
                        else:
                            logger.warning("No output found in response")

                        return response_json
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode JSON response: {e}")
                        return None
                else:
                    logger.warning(f"Unexpected status code: {response.status_code}")
                    return None

            except httpx.TimeoutException as e:
                logger.error(
                    f"❌ Timeout Error: Request timed out after {timeout.read} seconds"
                )
                return None
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"❌ HTTP Status Error: {e.response.status_code} - {e.response.text}"
                )
                return None
            except httpx.HTTPError as e:
                logger.error(f"❌ HTTP Error: {e}")
                return None

    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        logger.exception("Stack trace:")
        return None


# ---------------------------------------------------------------------------------------------
# MCP server code


from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("aiva")

# Constants


async def query_aiva_api(query: str) -> dict[str, Any] | None:
    """Make a request to TM Forum AIVA AI Assistant.

    Args:
        query: The query string to send to AIVA

    Returns:
        Dict containing the response data or error information
    """
    logger.info("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    logger.info(f"Querying AIVA with: {query}")
    result = await call_reasoning_agent(query)
    logger.info(f"Result: {result}")
    logger.info("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    return result


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""


@mcp.tool()
async def query_aiva(query: str) -> str:
    """Query the TM Forum AIVA AI Assistant.

    Args:
        query: The query string to send to AIVA

    Returns:
        The response from AIVA or an error message
    """
    response = await query_aiva_api(query)
    if not response:
        return "Unable to fetch data from AIVA."

    # Assuming response is a dict with 'data' key containing the answer
    return response.get("output", {}).get("output", "No response from AIVA.")


if __name__ == "__main__":
    logger.info("Starting AIVA MCP Server")
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server shutting down")
    except Exception as e:
        logger.exception("Server error")
        sys.exit(1)
