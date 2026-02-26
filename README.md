# ContainerLab MCP Server

A Python MCP server for managing containerized network labs via the [ContainerLab API](https://github.com/srl-labs/clab-api-server).

Built for [NetClaw](https://github.com/automateyournetwork/netclaw) using [FastMCP](https://github.com/jlowin/fastmcp).

## Tools

| Tool | Description |
|------|-------------|
| `authenticate` | Authenticate with the ContainerLab API server (optional — auto-auth handles this) |
| `listLabs` | List all available labs |
| `deployLab` | Deploy a new lab with a topology definition |
| `inspectLab` | Get lab details, node status, management IPs |
| `execCommand` | Execute a command on one or all lab nodes |
| `destroyLab` | Destroy a lab and clean up resources |

## Prerequisites

A running [ContainerLab API server](https://github.com/srl-labs/clab-api-server) with a Linux user configured for authentication.

```bash
# On the ContainerLab host:
sudo groupadd -f clab_admins && sudo groupadd -f clab_api
sudo useradd -m -s /bin/bash netclaw 2>/dev/null || true
sudo usermod -aG clab_admins netclaw && sudo passwd netclaw

# If the API server runs in Docker, restart it to pick up the new user:
docker restart clab-api-server
```

## Installation

```bash
pip install -r requirements.txt
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAB_API_SERVER_URL` | `http://localhost:8080` | ContainerLab API server URL |
| `CLAB_API_USERNAME` | `admin` | API username |
| `CLAB_API_PASSWORD` | `password` | API password |

## Usage

### Standalone (stdio MCP server)

```bash
python3 -u clab_mcp_server.py
```

### With NetClaw's mcp-call.py

```bash
python3 mcp-call.py "python3 -u clab_mcp_server.py" listLabs '{}'
python3 mcp-call.py "python3 -u clab_mcp_server.py" deployLab '{"topologyContent":{"name":"demo","topology":{"nodes":{"srl1":{"kind":"nokia_srlinux","image":"ghcr.io/nokia/srlinux:latest"}},"links":[]}}}'
python3 mcp-call.py "python3 -u clab_mcp_server.py" inspectLab '{"labName":"demo","details":true}'
python3 mcp-call.py "python3 -u clab_mcp_server.py" execCommand '{"labName":"demo","nodeName":"srl1","command":"show version"}'
python3 mcp-call.py "python3 -u clab_mcp_server.py" destroyLab '{"labName":"demo","cleanup":true,"graceful":true}'
```

## Supported Node Kinds

ContainerLab supports a wide range of network operating systems. Common examples:

| Kind | Platform | Example Image |
|------|----------|---------------|
| `cisco_iosxr` | Cisco IOS XR | `ios-xr/xrd-control-plane:latest` |
| `cisco_iosxe` | Cisco IOS XE (Cat8000v) | `c8000v:latest` |
| `cisco_nxos` | Cisco NX-OS (Nexus 9000v) | `n9kv:latest` |
| `cisco_ftdv` | Cisco Firepower FTDv | `ftdv:latest` |
| `cisco_csr1000v` | Cisco CSR 1000v | `csr1000v:latest` |
| `nokia_srlinux` | Nokia SR Linux | `ghcr.io/nokia/srlinux:latest` |
| `ceos` | Arista cEOS | `ceos:latest` |
| `juniper_crpd` | Juniper cRPD | `crpd:latest` |
| `juniper_vjunosswitch` | Juniper vJunos Switch | `vrnetlab/vr-vjunosswitch:latest` |
| `juniper_vjunosrouter` | Juniper vJunos Router | `vrnetlab/vr-vjunosrouter:latest` |
| `frr` | FRRouting | `frrouting/frr:latest` |
| `linux` | Generic Linux | `alpine:latest` |
| `paloalto_panos` | Palo Alto PAN-OS | `panos:latest` |
| `fortinet_fortigate` | Fortinet FortiGate | `fortigate:latest` |

For the full list, see the [ContainerLab documentation](https://containerlab.dev/manual/kinds/).

## License

MIT
