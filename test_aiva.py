# Standalone script to test the TM Forum AIVA API

import asyncio
import json
import sys
from aiva_api import query_aiva_api

# Define example queries
user_query = "Describe ODF"
# user_query = "List all the TMF Open-APIs"
# user_query = "Can you give me the code for Product catalogue management version 4? use swagger gen tool and generate for python-flask"


async def test_aiva():
    """Test the AIVA API with a sample query."""
    response = await query_aiva_api(user_query)

    if response:
        print("✅ Response:", file=sys.stderr)
        # save the response to a file
        with open("response.json", "w") as f:
            json.dump(response, f, indent=2)
        print("=================================================", file=sys.stderr)
        print("Output", file=sys.stderr)
        print(response.get("output", {}).get("output"), file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(test_aiva())
