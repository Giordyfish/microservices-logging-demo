#!/usr/bin/env python3
"""
Workspace initialization script.
Creates a virtual environment and installs uv package manager and project dependencies inside it.
"""

import subprocess
import sys
import platform
from pathlib import Path


def run_command(cmd, shell=False, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        raise


def check_python_version():
    """Ensure Python version meets requirements."""
    required_version = (3, 10)
    current_version = sys.version_info[:2]

    if current_version < required_version:
        print(f"Error: Python {required_version[0]}.{required_version[1]}+ required, "
              f"but {current_version[0]}.{current_version[1]} found.")
        sys.exit(1)

    print(f"[OK] Python {current_version[0]}.{current_version[1]} detected")


def get_venv_paths():
    """Get virtual environment paths based on OS."""
    venv_dir = Path(".venv")
    system = platform.system()

    if system == "Windows":
        python_path = venv_dir / "Scripts" / "python.exe"
        pip_path = venv_dir / "Scripts" / "pip.exe"
    else:
        python_path = venv_dir / "bin" / "python"
        pip_path = venv_dir / "bin" / "pip"

    return venv_dir, python_path, pip_path


def create_virtual_environment():
    """Create a virtual environment using venv."""
    venv_dir, python_path, _ = get_venv_paths()

    if venv_dir.exists():
        print("[OK] Virtual environment already exists")
        return python_path

    print("Creating virtual environment...")
    run_command([sys.executable, "-m", "venv", ".venv"])
    print("[OK] Virtual environment created")

    return python_path


def install_uv_in_venv(python_path):
    """Install uv package manager inside the virtual environment."""
    print("Installing uv in virtual environment...")

    # First ensure pip is up to date
    run_command([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])

    # Install uv
    run_command([str(python_path), "-m", "pip", "install", "uv"])

    print("[OK] uv installed successfully in virtual environment")


def install_dependencies():
    """Install project dependencies using uv inside the virtual environment."""
    print("Installing project dependencies...")

    venv_dir, _, _ = get_venv_paths()
    system = platform.system()

    if system == "Windows":
        uv_path = venv_dir / "Scripts" / "uv.exe"
    else:
        uv_path = venv_dir / "bin" / "uv"

    # Install in editable mode with all dependencies
    run_command([str(uv_path), "pip", "install", "-e", "."])

    print("[OK] Dependencies installed successfully")


def main():
    """Main initialization workflow."""
    print("=" * 50)
    print("Initializing workspace...")
    print("=" * 50)

    # Check Python version
    check_python_version()

    # Create virtual environment
    python_path = create_virtual_environment()

    # Install uv inside the venv
    install_uv_in_venv(python_path)

    # Install dependencies
    install_dependencies()

    print("\n" + "=" * 50)
    print("[OK] Workspace initialized successfully!")
    print("=" * 50)

    # Print activation instructions
    system = platform.system()
    if system == "Windows":
        activate_cmd = ".venv\\Scripts\\activate"
    else:
        activate_cmd = "source .venv/bin/activate"

    print(f"\nTo activate the virtual environment, run:\n  {activate_cmd}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Initialization failed: {e}")
        sys.exit(1)
