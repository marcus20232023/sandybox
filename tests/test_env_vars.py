import pytest
import podman
import logging

def test_environment_variables():
    """
    Verify that environment variables are correctly passed to the container.
    """
    try:
        client = podman.PodmanClient()
    except Exception as e:
        pytest.skip(f"Podman not available: {e}")

    env_vars = {"MY_VAR": "Hello World", "ANOTHER_VAR": "12345"}
    
    print("Starting env var test container...")
    
    try:
        container = client.containers.run(
            image="ubuntu:24.04",
            command=["bash", "-c", "echo $MY_VAR && echo $ANOTHER_VAR"],
            remove=True,
            environment=env_vars
        )
        output = container.decode("utf-8").strip().splitlines()
        assert output[0] == "Hello World"
        assert output[1] == "12345"
        print("Env var test passed.")
        
    except Exception as e:
        pytest.fail(f"Failed to run container with env vars: {e}")
