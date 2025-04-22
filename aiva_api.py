# AIVA API module for making requests to TM Forum AIVA AI Assistant
import logging
from pathlib import Path
import json
import httpx
from httpx import Timeout
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from typing import Any

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logger = logging.getLogger("aiva-api")

# Constants
SERVICE_ACCOUNT_FILE = "C:\\Dev\\lesterthomas\\MCP-AIVA\\vodafone-key.json"
API_URL = "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/982845833565/locations/us-central1/reasoningEngines/156728785469702144:query"

def get_access_token():
    """Get access token from service account credentials.
    
    Returns:
        str: The access token for API authentication
    """
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
                logger.info("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
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
                logger.error(f"❌ Timeout Error: Request timed out after {timeout.read} seconds")
                return None
            except httpx.HTTPStatusError as e:
                logger.error(f"❌ HTTP Status Error: {e.response.status_code} - {e.response.text}")
                return None
            except httpx.HTTPError as e:
                logger.error(f"❌ HTTP Error: {e}")
                return None

    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        logger.exception("Stack trace:")
        return None