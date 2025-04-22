# Standalone script to test the TM Forum AIVA API


import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import httpx
import asyncio
import sys
from httpx import Timeout, TransportError

# Path to the JSON service-account key file
SERVICE_ACCOUNT_FILE = "vodafone-key.json"

# Reasoning Engine endpoint URL
API_URL = "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/982845833565/locations/us-central1/reasoningEngines/156728785469702144:query"

# Define the user query
user_query = "Describe ODF"
# user_query = "List all the TMF Open-APIs"
user_query = "Can you give me the code for Product catalogue management version 4? use swagger gen tool and generate for python-flask"


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


# Update main to handle async
if __name__ == "__main__":
    asyncio.run(call_reasoning_agent(user_query))

# %%
