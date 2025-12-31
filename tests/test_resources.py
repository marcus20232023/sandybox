import pytest
import podman
import logging

# We assume the server code logic for kwargs is correct, 
# but we want to verify the underlying podman client accepts these arguments.

def test_resource_limits():
    """
    Verify that the installed podman library and runtime support 
    mem_limit and nano_cpus arguments.
    """
    try:
        client = podman.PodmanClient()
    except Exception as e:
        pytest.skip(f"Podman not available: {e}")

    # Test Memory Limit (e.g. 128MB)
    # Test CPU Limit (e.g. 0.5 CPU)
    
    # Note: We are using the python client directly here to match 
    # what the server does.
    
    print("Starting resource limit test container...")
    
    try:
        container = client.containers.run(
            image="ubuntu:24.04",
            command=["echo", "Resources OK"],
            remove=True,
            mem_limit="128m",
            nano_cpus=int(0.5 * 1_000_000_000)
        )
        output = container.decode("utf-8").strip()
        assert output == "Resources OK"
        print("Resource limit test passed.")
        
    except Exception as e:
        pytest.fail(f"Failed to run container with resource limits: {e}")
