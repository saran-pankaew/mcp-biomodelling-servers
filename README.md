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

## Claude Code Configuration

This is a project-level configuration. The file is located at:

```text
mcp-biomodelling-servers/.mcp.json
```

From the repository root, create or open it with:

```bash
code .mcp.json
```

You can also find it in the VS Code Explorer after enabling **Show Excluded
Files** if hidden files are not visible. Add the following content:

```json
{
  "mcpServers": {
    "neko": {
      "type": "stdio",
      "command": "${CLAUDE_PROJECT_DIR}/.venv/bin/mcp-neko-server"
    },
    "maboss": {
      "type": "stdio",
      "command": "${CLAUDE_PROJECT_DIR}/.venv/bin/mcp-maboss-server"
    },
    "physicell": {
      "type": "stdio",
      "command": "${CLAUDE_PROJECT_DIR}/.venv/bin/mcp-physicell-server"
    }
  }
}
```

Alternatively, add the servers from the repository root with Claude Code:

```bash
claude mcp add --transport stdio --scope project neko -- \
  "$PWD/.venv/bin/mcp-neko-server"
claude mcp add --transport stdio --scope project maboss -- \
  "$PWD/.venv/bin/mcp-maboss-server"
claude mcp add --transport stdio --scope project physicell -- \
  "$PWD/.venv/bin/mcp-physicell-server"
```

The project scope stores the shared configuration in `.mcp.json`. Start Claude
Code from the repository root:

```bash
claude
```

Inside Claude Code, run `/mcp` to approve and confirm the three servers are
connected. This command opens Claude Code's MCP configuration/status panel.
You can also check the project configuration from the terminal:

```bash
claude mcp list
```

The `.mcp.json` file uses project-relative paths through `CLAUDE_PROJECT_DIR`,
so it can be committed and shared with the team.

## Tests

```bash
source .venv/bin/activate
python -m pytest tests/ -q
```
