# build_gui.py — PyInstaller build script for Tactile Data Tool
# Usage: python build_gui.py

import subprocess
import sys
import os
import shutil

def run_cmd(cmd):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    print(result.stdout)

def main():
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        run_cmd([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Install dependencies
    deps = ["pyserial", "pillow"]
    for dep in deps:
        print(f"Installing {dep}...")
        subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)

    # Clean previous builds
    for dir_name in ["build", "dist", "__pycache__"]:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}/")
            shutil.rmtree(dir_name)

    # Build command
    build_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--onefile",
        "--name", "Tactile Data Tool",
        "data_gui_tk.py"
    ]

    # Add icon if available
    if os.path.exists("icon.ico"):
        build_cmd.extend(["--icon", "icon.ico"])

    print("\n=== Building Tactile Data Tool ===")
    run_cmd(build_cmd)

    print("\n=== Build Complete ===")
    if os.path.exists("dist"):
        files = os.listdir("dist")
        print(f"Output files in dist/: {files}")
        
        # Show file size
        for f in files:
            path = os.path.join("dist", f)
            if os.path.isfile(path):
                size_mb = os.path.getsize(path) / (1024 * 1024)
                print(f"  {f}: {size_mb:.1f} MB")

if __name__ == "__main__":
    main()
