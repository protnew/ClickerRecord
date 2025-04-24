import os
import sys
import subprocess
import shutil
import locale
from pathlib import Path

APP_NAME = "ClickerRecord"  # Fixed name

def clean_previous_builds():
    """Clean up artifacts from previous builds."""
    print("Cleaning up previous builds...")
    
    folders_to_clean = ["dist", "build", "__pycache__"]
    spec_file = f"{APP_NAME}.spec"
    old_spec_files = ["clicker.spec", "clicker_v2.spec", "clicker_v2.1.spec", 
                      "clicker_v2.3.spec", "clicker_v2.4.spec", "clicker_v2.5.spec"]
    
    files_to_clean = [spec_file] + old_spec_files
    
    for folder in folders_to_clean:
        if os.path.exists(folder):
            print(f"  Removing folder {folder}")
            try:
                shutil.rmtree(folder)
            except Exception as e:
                print(f"  Warning: Failed to remove {folder}: {str(e)}")
                
    for file in files_to_clean:
        if os.path.exists(file):
            print(f"  Removing file {file}")
            try:
                os.remove(file)
            except Exception as e:
                print(f"  Warning: Failed to remove {file}: {str(e)}")

def build_exe():
    """Build the EXE file."""
    try:
        import PyInstaller
        print(f"Found PyInstaller version {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    print("\nStarting EXE build process...")
    
    cmd = [
        "pyinstaller",
        f"--name={APP_NAME}",
        "--onefile",
        "--windowed",
        "--clean",
        "--icon=icon.ico",
        "--noconfirm",
        "--noupx",
        "--noconsole",
        "--log-level=WARN",
        f"--add-data={os.path.abspath('icon.ico')};.",
        "main.py"
    ]
    
    print(f"\nBuild command: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding=locale.getpreferredencoding(False), errors='ignore')
    
    exe_path_in_dist = os.path.abspath(os.path.join("dist", f"{APP_NAME}.exe"))
    final_exe_path = os.path.abspath(f"{APP_NAME}.exe")
    
    if result.returncode == 0 and os.path.exists(exe_path_in_dist):
        print(f"\nBuild successful: {exe_path_in_dist}")
        try:
            print(f"Moving {exe_path_in_dist} -> {final_exe_path}")
            if os.path.exists(final_exe_path):
                os.remove(final_exe_path)
            shutil.move(exe_path_in_dist, final_exe_path)
            size_mb = os.path.getsize(final_exe_path) / (1024 * 1024)
            print(f"EXE file created: {final_exe_path}")
            print(f"File size: {size_mb:.2f} MB")
            return True
        except Exception as e:
            print(f"Error moving {APP_NAME}.exe: {e}")
            return False
    else:
        print("Build failed!")
        print(f"Return code: {result.returncode}")
        print(f"Checked path: {exe_path_in_dist}")
        print(f"Standard output:\n{result.stdout}")
        if result.stderr:
            print(f"Errors:\n{result.stderr}")
        return False

def cleanup_build_files():
    """Clean up temporary build files after moving the EXE."""
    print("\nCleaning up temporary build files...")
    folders_to_clean = ["dist", "build"]
    spec_file = f"{APP_NAME}.spec"

    for folder in folders_to_clean:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"  Removed folder {folder}")
            except Exception as e:
                print(f"  Warning: Failed to remove folder {folder}: {e}")

    if os.path.exists(spec_file):
        try:
            os.remove(spec_file)
            print(f"  Removed file {spec_file}")
        except Exception as e:
            print(f"  Warning: Failed to remove file {spec_file}: {e}")

def main():
    print("=" * 60)
    print(f"Building application '{APP_NAME}'")
    print("=" * 60)
    
    clean_previous_builds()
    
    if build_exe():
        cleanup_build_files()
        print("\nAll operations completed successfully!")
        print(f"File {APP_NAME}.exe created in the current directory.")
    else:
        print("\nEXE build failed! Temporary files might remain.")
    
    print("=" * 60)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()