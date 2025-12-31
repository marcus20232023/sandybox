import pytest
import podman
import logging

def test_commit_flow():
    """
    Verify detach=True, wait, logs, commit, remove flow.
    """
    try:
        client = podman.PodmanClient()
    except Exception as e:
        pytest.skip(f"Podman not available: {e}")

    image_name = "sandybox-test-commit"
    
    # Clean up if exists
    try:
        client.images.remove(f"{image_name}:latest")
    except:
        pass

    print("Starting container detached...")
    
    try:
        # Run a container that touches a file in /root
        container = client.containers.run(
            image="ubuntu:24.04",
            command=["touch", "/root/artifact"],
            detach=True,
            remove=False 
        )
        
        # Wait for it to finish
        exit_code = container.wait()
        print(f"Container finished with exit code: {exit_code}")
        
        # Get logs
        logs = container.logs(stdout=True, stderr=True)
        # logs might be bytes or iterator
        if hasattr(logs, '__iter__') and not isinstance(logs, bytes):
             logs = b"".join(logs)
        print(f"Logs: {logs.decode('utf-8')}")
        
        # Commit
        print(f"Committing to {image_name}...")
        container.commit(repository=image_name)
        
        # Remove container
        container.remove()
        print("Container removed.")
        
        # Verify image exists and has the artifact
        print("Verifying image...")
        verifier = client.containers.run(
            image=f"{image_name}:latest",
            command=["ls", "/root/artifact"],
            remove=True
        )
        output = verifier.decode('utf-8').strip()
        assert output == "/root/artifact"
        print("Verification successful: artifact found in committed image.")

    except Exception as e:
        pytest.fail(f"Commit flow failed: {e}")
    finally:
        # Cleanup image
        try:
            client.images.remove(image_name)
        except:
            pass
