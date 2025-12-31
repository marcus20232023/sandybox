import os
import sys
import logging
import podman
from mcp.server.fastmcp import FastMCP
from pathlib import Path
from typing import List, Optional, Dict

# Configure Logging to STDERR (to avoid breaking MCP JSON-RPC on STDOUT)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("sandybox")

# Initialize FastMCP server
mcp = FastMCP("Sandybox")

# Podman client (rootless)
try:
    client = podman.PodmanClient()
    version = client.version()
    logger.info(f"Connected to Podman v{version.get('Version')}")
except Exception as e:
    logger.error(f"Failed to connect to Podman: {e}")
    # We continue, but tools might fail

# Configuration
WORKSPACE_ROOT = Path.home() / ".sandybox" / "workspaces"
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
logger.info(f"Workspace root set to: {WORKSPACE_ROOT}")

def get_workspace_path(workspace_id: str) -> Path:
    """Securely resolves a workspace path, preventing traversal attacks."""
    path = (WORKSPACE_ROOT / workspace_id).resolve()
    if not path.is_relative_to(WORKSPACE_ROOT):
        logger.warning(f"Security Alert: Path traversal attempt for ID '{workspace_id}'")
        raise ValueError(f"Invalid workspace ID: {workspace_id}")
    return path

@mcp.tool()
def create_workspace(workspace_id: str) -> str:
    """
    Creates a new persistent workspace directory.
    """
    logger.info(f"Tool Call: create_workspace(id={workspace_id})")
    try:
        path = get_workspace_path(workspace_id)
        if path.exists():
            msg = f"Workspace '{workspace_id}' already exists."
            logger.info(msg)
            return msg
        path.mkdir(parents=True)
        msg = f"Workspace '{workspace_id}' created at {path}"
        logger.info(msg)
        return msg
    except Exception as e:
        err_msg = f"Error creating workspace: {str(e)}"
        logger.error(err_msg)
        return err_msg

@mcp.tool()
def list_workspaces() -> str:
    """
    Lists all available workspaces.
    """
    logger.info("Tool Call: list_workspaces()")
    try:
        if not WORKSPACE_ROOT.exists():
            return "No workspaces found."
        workspaces = [d.name for d in WORKSPACE_ROOT.iterdir() if d.is_dir()]
        result = "\n".join(workspaces) if workspaces else "No workspaces found."
        return result
    except Exception as e:
        logger.error(f"Error listing workspaces: {e}")
        return f"Error listing workspaces: {str(e)}"

@mcp.tool()
def write_file(workspace_id: str, file_path: str, content: str) -> str:
    """
    Writes a file to a specific workspace.
    """
    logger.info(f"Tool Call: write_file(ws={workspace_id}, path={file_path}, size={len(content)} chars)")
    try:
        ws_path = get_workspace_path(workspace_id)
        # Check if workspace exists
        if not ws_path.exists():
             return f"Error: Workspace '{workspace_id}' does not exist. Create it first."

        full_path = (ws_path / file_path).resolve()
        if not full_path.is_relative_to(ws_path):
             return "Error: File path traversal detected."

        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return f"File written to {file_path} in workspace '{workspace_id}'"
    except Exception as e:
        logger.error(f"Error writing file: {e}")
        return f"Error writing file: {str(e)}"

@mcp.tool()
def read_file(workspace_id: str, file_path: str) -> str:
    """
    Reads a file from a specific workspace.
    """
    logger.info(f"Tool Call: read_file(ws={workspace_id}, path={file_path})")
    try:
        ws_path = get_workspace_path(workspace_id)
        full_path = (ws_path / file_path).resolve()
        
        if not full_path.exists():
            return f"Error: File '{file_path}' not found in workspace '{workspace_id}'"
        
        if not full_path.is_relative_to(ws_path):
             return "Error: File path traversal detected."

        content = full_path.read_text()
        logger.info(f"Read success: {len(content)} chars")
        return content
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return f"Error reading file: {str(e)}"

@mcp.tool()
def execute_command(
    command: str, 
    workspace_id: Optional[str] = None, 
    packages: Optional[List[str]] = None,
    image: str = "ubuntu:24.04",
    memory_limit: Optional[str] = None,
    cpu_count: Optional[float] = None,
    env_vars: Optional[Dict[str, str]] = None,
    commit_to_image: Optional[str] = None,
) -> str:
    """
    Executes a bash command in an ephemeral container.
    """
    logger.info(f"Tool Call: execute_command(ws={workspace_id}, image={image}, mem={memory_limit}, cpus={cpu_count}, commit={commit_to_image})")
    logger.info(f"Command: {command}")
    if packages:
        logger.info(f"Packages to install: {packages}")

    container = None
    try:
        mounts = []
        work_dir = "/"

        # Handle Workspace Mount
        if workspace_id:
            ws_path = get_workspace_path(workspace_id)
            if not ws_path.exists():
                return f"Error: Workspace '{workspace_id}' does not exist."
            
            mounts.append({
                "type": "bind",
                "source": str(ws_path),
                "target": "/workspace"
            })
            work_dir = "/workspace"

        # Construct the full bash command
        full_command = "export DEBIAN_FRONTEND=noninteractive && "
        
        # Install packages if requested
        if packages:
            pkg_str = " ".join(packages)
            # Try to install silently; on success print summary, on fail print error and exit
            install_cmd = (
                f"apt-get update -qq >/dev/null 2>&1 && "
                f"apt-get install -y -qq -o Dpkg::Use-Pty=0 {pkg_str} >/dev/null 2>&1"
            )
            full_command += f"({install_cmd} && echo '[System] Installed packages: {pkg_str}') || (echo '[System] Package installation failed' && exit 1) && "
        
        full_command += command

        # Prepare run arguments
        run_kwargs = {}
        if memory_limit:
            run_kwargs["mem_limit"] = memory_limit
        if cpu_count:
            # nano_cpus expects integer nanoseconds (1 CPU = 1e9)
            run_kwargs["nano_cpus"] = int(cpu_count * 1_000_000_000)
        if env_vars:
            run_kwargs["environment"] = env_vars

        logger.info("Spawning container...")
        # Run detached to allow commit later
        container = client.containers.run(
            image=image,
            command=["bash", "-c", full_command],
            remove=False, # We manage removal manually
            detach=True,
            mounts=mounts,
            working_dir=work_dir,
            **run_kwargs
            # network_mode defaults to bridge, allowing internet access
        )
        
        # Wait for completion
        exit_code = container.wait()
        logger.info(f"Container exited with code: {exit_code}")

        # Fetch logs
        logs = container.logs(stdout=True, stderr=True)
        # logs might be bytes or iterator depending on podman-py version/config
        if hasattr(logs, '__iter__') and not isinstance(logs, bytes):
             logs = b"".join(logs)
        output = logs.decode("utf-8")
        
        # Commit if requested
        if commit_to_image:
            logger.info(f"Committing container to image: {commit_to_image}")
            container.commit(repository=commit_to_image)
            output += f"\n[System] Snapshot saved as: {commit_to_image}"

        logger.info(f"Container execution finished. Output length: {len(output)} chars")
        return output

    except Exception as e:
        logger.error(f"Execution failed: {e}")
        return f"Error executing command: {str(e)}"
    finally:
        if container:
            try:
                container.remove()
            except Exception as e:
                logger.warning(f"Failed to remove container: {e}")

def main():
    mcp.run()

if __name__ == "__main__":
    main()
