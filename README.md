# MCP-AIVA
MCP server for the TM Forum AIVA AI Assistant

To use this locally with Claude Desktop, use the settings:


```
{
  "mcpServers": {
    "aiva": {
      "command": "uv",
      "args": [
        "--directory",
        "FULL_PATH_TO/MCP-AIVA",
        "run",
        "aiva-mcp-server.py"
      ]
    }
  }
}
```


For debugging, you can execute using the MCP Inspector with:

```
npx @modelcontextprotocol/inspector uv --directory FULL-PATH-TO/MCP-AIVA/  run aiva-mcp-server.py
```


An example query is:
```
What specific TM Forum API are required to implement the TM Forum Wholesale Broadband standard? Show the result as a table.
```

Here are example outputs in both Claude desktop and VSCode:

![Claude](images/Claude.png)

![VSCode](images/VSCode-1.png)

![VSCode](images/VSCode-2.png)