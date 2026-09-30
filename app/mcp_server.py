from mcp.server.mcpserver import MCPServer

mcp = MCPServer(
    "devboard",
    instructions=(
        "Devboard ticket control. Find IDs first: list_teams, then list_project "
        "with a team_id, then list_tickets with team_id and project_id."
    ),
)
