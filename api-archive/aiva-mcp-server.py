# print to std error
import sys

print("AIVA MCP Server", file=sys.stderr)

# ---------------------------------------------------------------------------------------------
# AIVA API Calling


import json
import httpx
from httpx import Timeout, TransportError
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# Path to the JSON service-account key file
SERVICE_ACCOUNT_FILE = "vodafone-key.json"

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
    """Make an async request to the reasoning agent."""
    token = get_access_token()
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
    async with httpx.AsyncClient(
        timeout=timeout,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
    ) as client:
        try:
            response = await client.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()

            if response.status_code == 200:
                print("✅ Response:", file=sys.stderr)
                # save the response to a file
                with open("response.json", "w") as f:
                    json.dump(response.json(), f, indent=2)
                print(
                    "=================================================", file=sys.stderr
                )
                print("Output", file=sys.stderr)
                print(response.json()["output"]["output"], file=sys.stderr)
                return response.json()
        except httpx.TimeoutException as e:
            print(
                f"❌ Timeout Error: Request timed out after {timeout.read} seconds",
                file=sys.stderr,
            )
            return None
        except httpx.HTTPError as e:
            print(f"❌ HTTP Error: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"❌ Exception: {e}", file=sys.stderr)
            return None


# ---------------------------------------------------------------------------------------------
# Unit test for this script as a standalone module.


async def test_call_reasoning_agent():
    """Test the call_reasoning_agent function."""
    query = "Describe ODF"
    # user_query = "List all the TMF Open-APIs"
    # user_query = "Can you give me the code for Product catalogue management version 4? use swagger gen tool."

    result = await call_reasoning_agent(query)
    if result:
        print("Test passed.")
    else:
        print("Test failed.")


import asyncio

# if __name__ == "__main__":
#     asyncio.run(test_call_reasoning_agent())
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
    print(
        "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++",
        file=sys.stderr,
    )
    print(f"Querying AIVA with: {query}", file=sys.stderr)
    result = await call_reasoning_agent(query)
    print(f"Result: {result}", file=sys.stderr)
    print(
        "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++",
        file=sys.stderr,
    )
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
    # Initialize and run the server
    mcp.run(transport="stdio")
