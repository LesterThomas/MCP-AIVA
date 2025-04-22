import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# Path to the JSON service-account key file
SERVICE_ACCOUNT_FILE = "vodafone-key.json"

# Reasoning Engine endpoint URL
API_URL = "https://us-central1-aiplatform.googleapis.com/v1beta1/projects/982845833565/locations/us-central1/reasoningEngines/156728785469702144:query"

# Define the user query
user_query = "Describe ODF"
# user_query = "List all the TMF Open-APIs"
user_query = "Can you give me the code for Product catalogue management version 4? use swagger gen tool."


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


def call_reasoning_agent(query):
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"input": {"input": query}}

    response = requests.post(API_URL, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        print("✅ Response:")
        # save the response to a file
        with open("response.json", "w") as f:
            json.dump(response.json(), f, indent=2)
        print("=================================================")
        print("Output")
        print(response.json()["output"]["output"])
        print("=================================================")

        # additional_info = response.json()["output"]["intermediate_steps"][0][1]
        print("Document References")
        # document_references = additional_info[0]
        # if "answer" in document_references:
        #     print(document_references["answer"]["relatedQuestions"])
        #     for reference in document_references["answer"]["references"]:
        #         print(reference["chunkInfo"]["documentMetadata"]["uri"])
        # print("Web References")
        # web_references = additional_info[1]
        # if "answer" in web_references:
        #     print(web_references["answer"]["relatedQuestions"])
        #     for reference in web_references["answer"]["references"]:
        #         print(reference["chunkInfo"]["documentMetadata"]["uri"])
        print("=================================================")

    else:
        print(f"❌ Error {response.status_code}: {response.text}")


if __name__ == "__main__":
    call_reasoning_agent(user_query)

# %%
