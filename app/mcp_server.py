from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.server.mcpserver import MCPServer

from app.config import settings
from app.oauth.provider import DevBoardOAuthProvider

mcp = MCPServer(
    "devboard",
    instructions=(
        "Devboard ticket control. Find IDs first: list_teams, then list_project "
        "with a team_id, then list_tickets with team_id and project_id."
    ),
    auth_server_provider=DevBoardOAuthProvider(),
    auth=AuthSettings.model_validate(
        {
            "issuer_url": settings.PUBLIC_URL,
            "resource_server_url": f"{settings.PUBLIC_URL}/mcp",
            "validate_token_resource": False,
            "client_registration_options": ClientRegistrationOptions(enabled=True),
        }
    ),
)
