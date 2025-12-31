# Sandybox (The Safe Agent Playground)

**Sandybox** is an MCP (Model Context Protocol) server that provides an isolated, persistent environment for AI agents to safely execute code and manipulate files. It uses **rootless Podman** containers to ensure security while maintaining a "local VM" feel.

## Key Features

*   **🛡️ Secure Isolation:** Executes code in ephemeral Ubuntu containers using rootless Podman.
*   **💾 Persistence:** Workspaces are stored on the host and mounted into containers, allowing data to persist across execution calls.
*   **📦 Dynamic Dependencies:** Agents can install `apt` packages on-the-fly for their tasks.
*   **📂 File Management:** Read and write files securely within the isolated workspace.
*   **🔌 MCP Standard:** Built on the Model Context Protocol, compatible with any MCP client (Claude Desktop, Gemini, etc.).

## Prerequisites

*   **Linux OS** (Recommended) or system with Podman support.
*   **Podman:** Must be installed and running in rootless mode.
    *   Verify with: `systemctl --user status podman.socket`
*   **Python 3.12+**
*   **uv:** For dependency management (optional but recommended).

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/marcus20232023/sandybox.git
    cd sandybox
    ```

2.  **Install dependencies:**
    Using `uv`:
    ```bash
    uv sync
    ```
    Or using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### MCP Configuration (Recommended)

To run Sandybox directly without manually cloning or installing dependencies, use `uvx` (part of the `uv` toolkit).

Add this to your MCP client configuration (e.g., `claude_desktop_config.json` or `mcpservers.json`):

```json
{
  "mcpServers": {
    "sandybox": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/marcus20232023/sandybox.git",
        "sandybox"
      ]
    }
  }
}
```

*Note: Replace `yourusername` with your actual GitHub username.*

### Manual Development

If you are developing Sandybox locally:

```bash
uv run src/sandybox/server.py
```

## Available Tools

*   `create_workspace(workspace_id: str)`: Creates a new persistent workspace directory.
*   `list_workspaces()`: Lists all active workspaces.
*   `write_file(workspace_id: str, file_path: str, content: str)`: Writes a file to a specific workspace.
*   `read_file(workspace_id: str, file_path: str)`: Reads a file from a workspace.
*   `execute_command(command: str, workspace_id: str, packages: [str])`: Runs a bash command in a container.
    *   Mounts the workspace to `/workspace`.
    *   Installs specified `packages` (e.g., `['curl', 'git']`) before execution.

## Security

*   **Rootless:** Containers run as your user, preventing root access to your host system.
*   **Path Traversal Protection:** File operations are strictly confined to the workspace directory.
*   **Ephemeral Containers:** Containers are destroyed immediately after execution, leaving no background processes.

## License

MIT
