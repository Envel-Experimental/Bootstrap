import subprocess

def build_executable(script_path):
    subprocess.run([
        "pyinstaller",
        "--onefile",
        "--noconsole",
        "--clean",
        "--icon", "icon.png",
        script_path
    ])

script_path = "bootstrap.py"

build_executable(script_path)
