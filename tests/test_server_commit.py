import pytest
from sandybox.server import execute_command
import podman

def test_execute_command_normal():
    """
    Test normal execution of execute_command.
    """
    output = execute_command(command="echo Hello")
    assert "Hello" in output

def test_execute_command_with_commit():
    """
    Test execute_command with commit_to_image.
    """
    image_name = "sandybox-server-test"
    client = podman.PodmanClient()
    
    # Clean up
    try:
        client.images.remove(f"{image_name}:latest")
    except:
        pass

    output = execute_command(
        command="touch /root/server_test_artifact", 
        commit_to_image=image_name
    )
    
    assert "[System] Snapshot saved as" in output
    
    # Verify image exists
    print("Verifying committed image...")
    verifier = client.containers.run(
        image=f"{image_name}:latest",
        command=["ls", "/root/server_test_artifact"],
        remove=True
    )
    assert "/root/server_test_artifact" in verifier.decode("utf-8")
    
    # Cleanup
    try:
        client.images.remove(f"{image_name}:latest")
    except:
        pass
