import os
import subprocess
import sys
import shutil

def build():
    print("🚀 Starting SortAI Pro Packaging...")
    
    # Identify CustomTkinter path
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    print(f"📦 Found CustomTkinter at: {ctk_path}")

    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name=SortAI",
        "--add-data", f"{ctk_path}{os.pathsep}customtkinter",  # Bundle CTK themes
        "main.py"
    ]

    print(f"🛠️ Executing: {' '.join(cmd)}")
    # Run without capture to see live progress if possible, or just run it
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("✅ Build Successful!")
        print(f"📂 Your executable is ready in: {os.path.abspath('dist/SortAI.exe')}")
        
        # Cleanup
        print("🧹 Cleaning up build artifacts...")
        if os.path.exists("build"): shutil.rmtree("build")
        if os.path.exists("SortAI.spec"): os.remove("SortAI.spec")
    else:
        print("❌ Build Failed!")
        print(result.stdout)
        print(result.stderr)

if __name__ == "__main__":
    build()
