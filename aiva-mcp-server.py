# MCP Server implementation on top of TM Forum AI Assistant (AIVA).
# This script sets up a FastMCP server that interacts with the AIVA API to handle queries and responses.

# logging and system imports
import logging
import sys
from pathlib import Path

# AIVA API Calling imports
import json
import httpx
from httpx import Timeout
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# MCP Server imports
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------------------------
# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "aiva-mcp-server.log"),
    ],
)

logger = logging.getLogger("aiva-mcp")
logger.info("AIVA MCP Server")

# ---------------------------------------------------------------------------------------------
# AIVA API Calling

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


async def query_aiva_api(query: str) -> dict[str, Any] | None:
    """Make an async request to TM Forum AIVA AI Assistant.

    Args:
        query: The query string to send to AIVA

    Returns:
        Dict containing the response data or error information

    Raises:
        Various httpx exceptions are caught and logged
    """

    logger.info("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    logger.info(f"Querying AIVA with: {query}")

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
                logger.info(f"response: {response}")
                logger.info(
                    "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
                )
                response.raise_for_status()

                if response.status_code == 200:
                    try:
                        response_json = response.json()
                        logger.info("✅ Response received successfully")

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

# Initialize FastMCP server
mcp = FastMCP("aiva")


# Resources
@mcp.resource("apis://categories")
async def get_api_categories() -> str:
    """Get the main categories of TM Forum Open APIs."""
    return """TM Forum Open APIs are organized into these main categories:

1. Customer Management APIs
   - Customer management, engagement, and experience
   - Party management and privacy

2. Product Management APIs
   - Product catalog and inventory
   - Product ordering and qualification
   - Product specifications and offering management
   - Product Quote management
   - Product Configuration management

3. Service Management APIs
   - Service catalog and inventory
   - Service ordering and activation
   - Service quality management
   - Service problem management
   - Service test management
   - Service performance management
   - Service Level Agreement management
   - Service Level Assurance management

4. Resource Management APIs
   - Resource catalog and inventory
   - Resource ordering and activation
   - Resource function management
   - Resource performance management
   - Resource trouble management

5. Common APIs
   - Event management
   - Notification management
   - Alarm management
   - Usage management
   - Audit Management
   - Authorization Management
   - Identity Management
   """


@mcp.resource("knowledge://frameworks")
async def get_frameworks() -> str:
    """Get information about key TM Forum frameworks."""
    return """Key TM Forum frameworks include:

1. Open Digital Architecture (ODA)
   - Component-based architecture
   - Open APIs and standard interfaces
   - Cloud-native design principles

2. Business Process Framework (eTOM)
   - End-to-end business processes
   - Operations and strategy mapping
   - Process decomposition

3. Information Framework (SID)
   - Common information model
   - Business entity definitions
   - Data model standards

4. Application Framework (TAM)
   - Application component mapping
   - System integration patterns
   - Application capabilities"""


# Example prompts
@mcp.prompt()
def api_list_prompt() -> str:
    """Get a list of all TM Forum Open APIs."""
    return "List all the TM Forum Open APIs and their main purposes."


@mcp.prompt()
def api_list_prompt_subsection() -> str:
    """Query APIs for a specific area."""
    return "What specific TM Forum API are required to implement the TM Forum Wholesale Broadband standard?"


@mcp.prompt()
def api_details_prompt() -> str:
    """Get detailed information about a specific TM Forum API."""
    return "What are the key features and capabilities of TMF620 Product Catalog Management API?"


@mcp.prompt()
def standards_prompt() -> str:
    """Get information about TM Forum standards for a specific domain."""
    return "What specific TM Forum APIs are required to implement the TM Forum Wholesale Broadband standard?"


@mcp.prompt()
def best_practices_prompt() -> str:
    """Get TM Forum best practices for implementation."""
    return "What are the best practices for implementing TMF620 Product Catalog Management API?"


@mcp.tool()
async def query_tmforum_ai_assistant(query: str) -> str:
    """Get information from the TM Forum knowledge base using AIVA AI Assistant.

    Queries the TM Forum AIVA AI Assistant to retrieve expert knowledge about TM Forum standards,
    APIs, frameworks, and best practices.

    Args:
        query: A natural language question about TM Forum topics (e.g., standards, APIs, frameworks)

    Returns:
        str: AIVA's response containing relevant TM Forum information or an error message if the query fails
    """
    response = await query_aiva_api(query)
    if not response:
        return "Unable to fetch data from AIVA."

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
