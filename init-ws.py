#!/usr/bin/env python3
"""
Workspace initialization script.

Each service now owns its own virtual environment and dependency graph. This
script simply orchestrates those per-service initializers so the entire
workspace can be bootstrapped with a single command.
"""

import subprocess
import sys
import os
import json
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).parent.resolve()
SERVICES_DIR = REPO_ROOT / "services"


def run_command(cmd, cwd=None):
    """Run a command in an optional working directory."""
    printable = " ".join(str(part) for part in cmd)
    location = f" (cwd={cwd})" if cwd else ""
    print(f"Running: {printable}{location}")
    subprocess.run(cmd, check=True, cwd=cwd)
    
def install_vscode_extensions():
    extensions_file = os.path.join(".vscode", "extensions.json")
    if not os.path.exists(extensions_file):
        print("No VSCode extensions file found.")
        return
    try:
        with open(extensions_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print("Error parsing extensions.json:", e)
        return
    recommendations = data.get("recommendations", [])
    if not recommendations:
        print("No VSCode extension recommendations found.")
        return

    code_cli = shutil.which("code")
    if not code_cli:
        print("VSCode CLI command 'code' not found; skipping extension installation.")
        return

    for ext in recommendations:
        print(f"Installing VSCode extension: {ext}")
        try:
            run_command([code_cli, "--install-extension", ext])
        except subprocess.CalledProcessError as exc:
            print(
                f"  [WARN] Failed to install {ext} (exit {exc.returncode}). "
                "Open the repo with 'code .' so VS Code connects to this WSL distro, "
                "then rerun init-ws.py."
            )


def check_python_version():
    """Ensure the host interpreter meets the minimum requirements."""
    required_major, required_minor = 3, 10
    if (sys.version_info.major, sys.version_info.minor) < (
        required_major,
        required_minor,
    ):
        raise SystemExit(
            f"Python {required_major}.{required_minor}+ is required, "
            f"but {sys.version_info.major}.{sys.version_info.minor} is active."
        )
    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor} detected")


def discover_service_initializers():
    """Return a sorted list of (service_name, init_script_path)."""
    if not SERVICES_DIR.exists():
        return []

    scripts = []
    for service_dir in sorted(SERVICES_DIR.iterdir()):
        if not service_dir.is_dir():
            continue
        init_script = service_dir / "init.py"
        if init_script.exists():
            scripts.append((service_dir.name, init_script))

    return scripts


def run_service_initializer(service_name, init_script):
    """Execute a service's init.py using the current Python interpreter."""
    banner = f"Initializing {service_name}"
    print("\n" + "=" * len(banner))
    print(banner)
    print("=" * len(banner))
    run_command([sys.executable, str(init_script)], cwd=init_script.parent)


def main():
    """Entry point for workspace initialization."""
    print("=" * 50)
    print("Installing recommended VSCode extensions")
    print("=" * 50)
    install_vscode_extensions()

    print("=" * 50)
    print("Initializing all service environments")
    print("=" * 50)

    check_python_version()

    service_initializers = discover_service_initializers()
    if not service_initializers:
        print("No service init.py scripts were found under the services directory.")
        return

    for service_name, init_script in service_initializers:
        run_service_initializer(service_name, init_script)

    print("\n" + "=" * 50)
    print("[OK] All service environments initialized successfully!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"\n[ERROR] Command failed with exit code {exc.returncode}")
        sys.exit(exc.returncode)
    except Exception as exc:
        print(f"\n[ERROR] Initialization failed: {exc}")
        sys.exit(1)
