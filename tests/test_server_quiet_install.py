import pytest
from sandybox.server import execute_command

def test_quiet_install():
    """
    Test that execute_command with packages installs successfully with the quiet flag.
    We can't easily assert on stdout 'noise' reduction here, but we can assert success.
    """
    # Using a small package 'nano' or 'curl'
    # 'curl' is often present, 'nano' might not be.
    # 'file' is small.
    output = execute_command(
        command="which file", 
        packages=["file"]
    )
    
    assert "/usr/bin/file" in output
    # Check that we don't see typical apt output like "Reading package lists..."
    # although -qq might still print errors, it shouldn't print "Reading package lists..."
    assert "Reading package lists..." not in output
