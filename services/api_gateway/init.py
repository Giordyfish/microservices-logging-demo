#!/usr/bin/env python3
"""
Initialize this service workspace by creating a dedicated virtual environment and
installing dependencies from requirements.txt using pip.
"""

import platform
import subprocess
import sys
from pathlib import Path


SERVICE_DIR = Path(__file__).parent.resolve()
SERVICE_NAME = SERVICE_DIR.name
VENV_DIR = SERVICE_DIR / ".venv"
REPO_ROOT = SERVICE_DIR.parents[1]
SHARED_DIR = REPO_ROOT / "shared"
REQUIREMENTS_FILE = SERVICE_DIR / "requirements.txt"


def run_command(cmd):
    """Run a command and stream its output."""
    printable = " ".join(str(part) for part in cmd)
    print(f"[{SERVICE_NAME}] $ {printable}")
    subprocess.run(cmd, check=True)


def ensure_python_version():
    """Ensure the host Python version satisfies the service constraints."""
    required = (3, 10)
    if sys.version_info < required:
        raise SystemExit(
            f"{SERVICE_NAME} requires Python {required[0]}.{required[1]}+, "
            f"but {sys.version_info.major}.{sys.version_info.minor} is active."
        )


def ensure_virtualenv():
    """Create the virtual environment if it does not already exist."""
    if VENV_DIR.exists():
        print(f"[{SERVICE_NAME}] Virtual environment already present at {VENV_DIR}")
        return

    print(f"[{SERVICE_NAME}] Creating virtual environment at {VENV_DIR}")
    run_command([sys.executable, "-m", "venv", str(VENV_DIR)])


def get_python_bin():
    """Return the path to the virtual environment's python interpreter."""
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def install_requirements(python_path):
    """Install service requirements using pip."""
    if not REQUIREMENTS_FILE.exists():
        print(f"[{SERVICE_NAME}] No requirements.txt found; skipping dependency install")
        return

    run_command([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])
    run_command([str(python_path), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])


def install_shared_package(python_path):
    """Install the shared utilities package in editable mode."""
    if not SHARED_DIR.exists():
        print(f"[{SERVICE_NAME}] Shared package directory not found; skipping install")
        return

    run_command([str(python_path), "-m", "pip", "install", "-e", str(SHARED_DIR)])


def main():
    """Entry point for service initialization."""
    ensure_python_version()
    ensure_virtualenv()
    python_path = get_python_bin()
    install_requirements(python_path)
    install_shared_package(python_path)

    activate_cmd = (
        f"{VENV_DIR / 'Scripts' / 'activate'}"
        if platform.system() == "Windows"
        else f"source {VENV_DIR}/bin/activate"
    )
    print(f"[{SERVICE_NAME}] Environment ready. Activate with:\n    {activate_cmd}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"[{SERVICE_NAME}] Command failed with exit code {exc.returncode}")
        raise
