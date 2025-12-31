import podman
from pathlib import Path
import shutil
import sys

# Replicate the Logic from server.py for testing purposes without starting the full MCP server
WORKSPACE_ROOT = Path.home() / ".sandybox" / "workspaces"
TEST_WS_ID = "test_workspace_123"
TEST_FILE = "hello.txt"

def setup():
    """Clean up previous test runs"""
    ws_path = WORKSPACE_ROOT / TEST_WS_ID
    if ws_path.exists():
        shutil.rmtree(ws_path)
    print("Cleaned up previous test artifacts.")

def test_workspace_creation():
    """Test creating a workspace directory"""
    print(f"\n--- Testing Workspace Creation ({TEST_WS_ID}) ---")
    ws_path = WORKSPACE_ROOT / TEST_WS_ID
    ws_path.mkdir(parents=True, exist_ok=True)
    
    if ws_path.exists():
        print("PASS: Workspace directory created.")
    else:
        print("FAIL: Workspace directory not found.")
        sys.exit(1)

def test_file_writing():
    """Test writing a file to the workspace"""
    print(f"\n--- Testing File Writing ({TEST_FILE}) ---")
    ws_path = WORKSPACE_ROOT / TEST_WS_ID
    file_path = ws_path / TEST_FILE
    content = "Hello from the host filesystem!"
    file_path.write_text(content)
    
    if file_path.read_text() == content:
        print("PASS: File written and verified.")
    else:
        print("FAIL: File content mismatch.")
        sys.exit(1)

def test_podman_execution():
    """Test running a container with the workspace mounted and checking the file"""
    print("\n--- Testing Podman Execution with Mount & Package Install ---")
    
    ws_path = WORKSPACE_ROOT / TEST_WS_ID
    client = podman.PodmanClient()
    
    # 1. Mount the workspace
    # 2. Install 'figlet' (ascii art text)
    # 3. Read the file we wrote earlier
    # 4. Use figlet to print "Sandybox"
    
    # Note: We need internet access for apt-get, so network_mode is default (bridge)
    
    command = (
        "export DEBIAN_FRONTEND=noninteractive && "
        "apt-get update && apt-get install -y figlet && "
        "echo '--- File Content ---' && "
        "cat hello.txt && " # We are in /workspace, so this should work
        "echo '\n--- Figlet Output ---' && "
        "figlet Sandybox"
    )
    
    mounts = [{
        "type": "bind",
        "source": str(ws_path),
        "target": "/workspace"
    }]
    
    try:
        print("Running container (pulling figlet takes a few seconds)...")
        output = client.containers.run(
            image="ubuntu:24.04",
            command=["bash", "-c", command],
            remove=True,
            detach=False,
            mounts=mounts,
            working_dir="/workspace"
        )
        
        decoded_output = output.decode("utf-8")
        print("\nContainer Output:")
        print(decoded_output)
        
        if "Hello from the host filesystem!" in decoded_output and "--- Figlet Output ---" in decoded_output:
            print("\nPASS: Container read file and installed package successfully.")
        else:
            print("\nFAIL: Output missing expected content.")
            print(f"DEBUG: 'Hello' found: {'Hello from the host filesystem!' in decoded_output}")
            print(f"DEBUG: 'Figlet' found: {'--- Figlet Output ---' in decoded_output}")
            sys.exit(1)

    except Exception as e:
        print(f"\nFAIL: Podman error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup()
    test_workspace_creation()
    test_file_writing()
    test_podman_execution()
