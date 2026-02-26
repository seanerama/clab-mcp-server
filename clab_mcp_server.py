#!/usr/bin/env python3
"""ContainerLab MCP Server — manage containerized network labs via the ContainerLab API.

Provides 6 tools: authenticate, listLabs, deployLab, inspectLab, execCommand, destroyLab.
Auto-authenticates on every call using CLAB_API_* environment variables.

Usage:
    python3 -u clab_mcp_server.py              # stdio MCP server
    python3 mcp-call.py "python3 -u clab_mcp_server.py" listLabs '{}'
"""

import json
import logging
import os
import sys
import time
from typing import Optional

import requests
from dotenv import load_dotenv
from fastmcp import FastMCP

# Logging to stderr only — stdout is reserved for MCP protocol
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("clab-mcp")

load_dotenv()

API_SERVER_URL = os.getenv("CLAB_API_SERVER_URL", "http://localhost:8080")
API_USERNAME = os.getenv("CLAB_API_USERNAME", "admin")
API_PASSWORD = os.getenv("CLAB_API_PASSWORD", "password")


class ClabApiClient:
    """HTTP client for the ContainerLab API server with auto-authentication."""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.token: Optional[str] = None
        self.token_expiry: float = 0

    def _ensure_auth(self):
        """Authenticate if token is missing or expired."""
        if self.token and time.time() < self.token_expiry:
            return
        resp = requests.post(
            f"{self.base_url}/login",
            json={"username": self.username, "password": self.password},
            timeout=15,
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"Authentication failed (HTTP {resp.status_code}): {resp.text}"
            )
        data = resp.json()
        self.token = data.get("token")
        if not self.token:
            raise RuntimeError(f"No token in login response: {data}")
        self.token_expiry = time.time() + 50 * 60  # 50 min cache

    def request(self, method: str, path: str, json_body=None, params=None):
        """Make an authenticated API request."""
        self._ensure_auth()
        resp = requests.request(
            method,
            f"{self.base_url}{path}",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            json=json_body,
            params=params,
            timeout=30,
        )
        return resp


# Initialize client and MCP server
client = ClabApiClient(API_SERVER_URL, API_USERNAME, API_PASSWORD)
mcp = FastMCP("ContainerLab MCP Server")


@mcp.tool()
def authenticate(apiServerURL: str, username: str, password: str) -> str:
    """Authenticate with the ContainerLab API server.

    Normally auto-authentication handles this. Use only if you need
    different credentials than what's in the environment.
    """
    client.base_url = apiServerURL.rstrip("/")
    client.username = username
    client.password = password
    client.token = None
    client.token_expiry = 0
    try:
        client._ensure_auth()
        return "Successfully authenticated with the API server"
    except RuntimeError as e:
        return f"ERROR: {e}"


@mcp.tool()
def listLabs() -> str:
    """List all available labs on the ContainerLab server."""
    resp = client.request("GET", "/api/v1/labs")
    if resp.status_code != 200:
        return f"ERROR: Failed to list labs (HTTP {resp.status_code}): {resp.text}"
    return json.dumps(resp.json(), indent=2)


@mcp.tool()
def deployLab(topologyContent: dict, reconfigure: bool = False) -> str:
    """Deploy a new lab with the provided topology definition.

    topologyContent must be a JSON object with name, topology (nodes + links).
    Set reconfigure=true to reconfigure an existing lab instead of failing on name conflict.
    """
    params = {}
    if reconfigure:
        params["reconfigure"] = "true"
    resp = client.request(
        "POST",
        "/api/v1/labs",
        json_body={"topologyContent": topologyContent},
        params=params or None,
    )
    if resp.status_code != 200:
        return f"ERROR: Failed to deploy lab (HTTP {resp.status_code}): {resp.text}"
    return f"Successfully deployed lab.\nResponse: {resp.text}"


@mcp.tool()
def inspectLab(labName: str, details: bool = False) -> str:
    """Get detailed information about a specific lab including node status and management IPs."""
    params = {}
    if details:
        params["details"] = "true"
    resp = client.request("GET", f"/api/v1/labs/{labName}", params=params or None)
    if resp.status_code != 200:
        return f"ERROR: Failed to inspect lab (HTTP {resp.status_code}): {resp.text}"
    return json.dumps(resp.json(), indent=2)


@mcp.tool()
def execCommand(labName: str, command: str, nodeName: Optional[str] = None) -> str:
    """Execute a command on one or all nodes in a lab.

    Specify nodeName to target a specific node, or omit to run on all nodes.
    """
    params = {}
    if nodeName:
        params["nodeFilter"] = nodeName
    resp = client.request(
        "POST",
        f"/api/v1/labs/{labName}/exec",
        json_body={"command": command},
        params=params or None,
    )
    if resp.status_code != 200:
        return f"ERROR: Failed to execute command (HTTP {resp.status_code}): {resp.text}"
    try:
        return json.dumps(resp.json(), indent=2)
    except Exception:
        return resp.text


@mcp.tool()
def destroyLab(labName: str, cleanup: bool = False, graceful: bool = False) -> str:
    """Destroy a lab and clean up all associated resources.

    Use graceful=true for clean node shutdown. Use cleanup=true to remove lab directory.
    """
    params = {}
    if cleanup:
        params["cleanup"] = "true"
    if graceful:
        params["graceful"] = "true"
    resp = client.request("DELETE", f"/api/v1/labs/{labName}", params=params or None)
    if resp.status_code != 200:
        return f"ERROR: Failed to destroy lab (HTTP {resp.status_code}): {resp.text}"
    try:
        data = resp.json()
        return data.get("message", json.dumps(data, indent=2))
    except Exception:
        return resp.text


if __name__ == "__main__":
    log.info("ContainerLab MCP Server started")
    log.info("API URL: %s", API_SERVER_URL)
    mcp.run()
