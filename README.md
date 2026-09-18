# MCP Bio-Modelling Servers

Version `2.3.0` of three MCP servers for biological modelling:

- **NeKo**: signalling-network construction and analysis
- **MaBoSS**: Boolean-network simulation
- **PhysiCell**: PhysiCell and PhysiBoSS configuration

## Requirements

- Python `3.10` to `3.14`
- [`uv`](https://docs.astral.sh/uv/)
- Graphviz, including the `dot` command

Check Graphviz with:

```bash
dot -V
```

## Install From This Repository

```bash
git clone https://github.com/saran-pankaew/mcp-biomodelling-servers.git
cd mcp-biomodelling-servers
git checkout development_v2

uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"
```

If the branch is different, replace `main` with the branch you want
to use.

## Update

```bash
git pull --ff-only origin main
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Run a Server

Run one command per server process:

```bash
mcp-neko-server
mcp-maboss-server
mcp-physicell-server
```

## MCP Client Configuration

Use the executable inside the virtual environment. Replace the path with the
absolute path on your machine.

In VS Code, open the Command Palette with `Cmd+Shift+P`, run `MCP: Open User
Configuration`, and add the servers below. For project-only settings, save the
same configuration in `.vscode/mcp.json`.

```json
{
  "servers": {
    "neko": {
      "type": "stdio",
      "command": "/path/to/mcp-biomodelling-servers/.venv/bin/mcp-neko-server"
    },
    "maboss": {
      "type": "stdio",
      "command": "/path/to/mcp-biomodelling-servers/.venv/bin/mcp-maboss-server"
    },
    "physicell": {
      "type": "stdio",
      "command": "/path/to/mcp-biomodelling-servers/.venv/bin/mcp-physicell-server"
    }
  }
}
```

## Tests

```bash
source .venv/bin/activate
python -m pytest tests/ -q
```
