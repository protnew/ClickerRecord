import os
import sys
import subprocess
import shutil
from pathlib import Path
import time

# Version and name variables no longer needed
# APP_VERSION = "v3.6"
# VERSION = "3.6"
APP_NAME = "ClickerRecord" # Fixed name

def clean_previous_builds():
    """Clean up artifacts from previous builds."""
    print("Cleaning up previous builds...")
    
    # Folders to clean
    folders_to_clean = ["dist", "build", "__pycache__"]
    
    # Spec file name is now fixed
    spec_file = f"{APP_NAME}.spec"
    # Old spec files (just in case they remain)
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
                
                # Additional attempt to delete files in the dist folder
                if folder == "dist":
                    try:
                        for file in os.listdir(folder):
                            file_path = os.path.join(folder, file)
                            try:
                                if os.path.isfile(file_path):
                                    os.unlink(file_path)
                                    print(f"    Removed file: {file_path}")
                            except Exception as e2:
                                print(f"    Failed to remove {file_path}: {str(e2)}")
                    except Exception:
                        pass
    
    for file in files_to_clean:
        if os.path.exists(file):
            print(f"  Removing file {file}")
            try:
                os.remove(file)
            except Exception as e:
                print(f"  Warning: Failed to remove {file}: {str(e)}")

def build_exe():
    """Build the EXE file."""
    # Check for PyInstaller
    try:
        import PyInstaller
        print(f"Found PyInstaller version {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    print("\nStarting EXE build process...")
    
    # PyInstaller parameters
    cmd = [
        "pyinstaller",
        f"--name={APP_NAME}",  # Using fixed name
        "--onefile",
        "--windowed",
        "--clean",
        "--icon=icon.ico",
        "--noconfirm",
        "--noupx",
        "--noconsole",
        "--log-level=WARN",
        # Ensure the icon is copied correctly
        f"--add-data={os.path.abspath('icon.ico')};.",
        "main.py"
    ]
    
    # Run the build process
    print(f"\nBuild command: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    
    # Process results
    exe_path_in_dist = os.path.abspath(os.path.join("dist", f"{APP_NAME}.exe"))
    final_exe_path = os.path.abspath(f"{APP_NAME}.exe") # Path in the current directory
    
    if result.returncode == 0 and os.path.exists(exe_path_in_dist):
        print(f"\nBuild successful: {exe_path_in_dist}")
        # Move the EXE to the current directory
        try:
            print(f"Moving {exe_path_in_dist} -> {final_exe_path}")
            # Remove old file in the current directory if it exists
            if os.path.exists(final_exe_path):
                os.remove(final_exe_path)
            shutil.move(exe_path_in_dist, final_exe_path)
            size_mb = os.path.getsize(final_exe_path) / (1024 * 1024)
            print(f"EXE file created: {final_exe_path}")
            print(f"File size: {size_mb:.2f} MB")
            return True # Return success
        except Exception as e:
            print(f"Error moving {APP_NAME}.exe: {e}")
            return False # Return failure
    else:
        print("Build failed!")
        print(f"Return code: {result.returncode}")
        print(f"Checked path: {exe_path_in_dist}")
        print(f"Standard output:\n{result.stdout}")
        if result.stderr:
            print(f"Errors:\n{result.stderr}")
        return False

# Function create_release_zip() REMOVED

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
    
    # 1. Clean previous artifacts (just in case)
    clean_previous_builds()
    
    # 2. Build and move EXE
    if build_exe():
        # 3. Final cleanup
        cleanup_build_files()
        print("\nAll operations completed successfully!")
        print(f"File {APP_NAME}.exe created in the current directory.")
    else:
        print("\nEXE build failed! Temporary files might remain.")
    
    print("=" * 60)
    # Remove input if the script should just run and exit
    # input("Press Enter to exit...") 

if __name__ == "__main__":
    # Ensure we run from the script's directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main() 