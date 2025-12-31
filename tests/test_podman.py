import podman
import sys

try:
    client = podman.PodmanClient()
    print("Checking Podman connection...")
    version = client.version()
    print(f"Podman Version: {version.get('Version')}")

    print("Pulling ubuntu:24.04 (this might take a moment if not present)...")
    client.images.pull("ubuntu:24.04")

    print("Running test container...")
    output = client.containers.run(
        "ubuntu:24.04",
        command=["echo", "Hello from Sandybox!"],
        remove=True
    )
    print(f"Output: {output.decode('utf-8').strip()}")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
