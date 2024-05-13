import os
import re
import shutil
import subprocess
import tempfile
import zipfile

import requests


class JavaVersion:
    def __init__(self, major, minor, build):
        self.major = major
        self.minor = minor
        self.build = build

    @classmethod
    def from_str(cls, version_str):
        parts = version_str.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid version format")
        return cls(int(parts[0]), int(parts[1]), parts[2])

    def __eq__(self, other):
        return self.major == other.major and self.minor == other.minor

    def __ge__(self, other):
        return (self.major, self.minor) >= (other.major, other.minor)

    def __str__(self):
        return f"{self.major}.{self.minor}"


def check_and_download_java():
    def execute_java_version_command():
        try:
            output = subprocess.check_output(["java", "-version"], stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return output
        except Exception as e:
            print(f"Error executing 'java -version': {e}")
            return None

    def get_java_version(output):
        try:
            match = re.search(r'\"(\d+\.\d+\.\d+).*\"', output)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"Error parsing Java version: {e}")
        return None

    def check_java_version(java_dir):
        java_version_output = execute_java_version_command()
        if java_version_output:
            print(f"Found installed Java version: {java_version_output}")
            java_version = get_java_version(java_version_output)
            if java_version:
                return java_version
        else:
            print("No installed Java found in system")

        if os.path.isdir(java_dir):
            java_executable_path = None
            for root, dirs, files in os.walk(java_dir):
                for file in files:
                    if file == "java" or file == "java.exe":
                        java_executable_path = os.path.join(root, file)
                        break

            if java_executable_path:
                print(f"Java executable found at: {java_executable_path}")
                try:
                    output = subprocess.check_output([java_executable_path, "-version"], stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    java_version = get_java_version(output)
                    print(f"Found Java version: {java_version}")
                    if java_version:
                        return java_version
                except Exception as e:
                    print(f"Error checking downloaded Java version: {e}")
            else:
                print(f"No Java executable found in directory: {java_dir}")

        return False

    def download_java(java_url, java_dir):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
            print(f"Downloading Java from {java_url} to {java_dir}")
            response = requests.get(java_url, headers=headers)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(response.content)
                tmp_file_path = tmp_file.name

            os.makedirs(java_dir, exist_ok=True)

            target_path = os.path.join(java_dir, os.path.basename(java_url))
            shutil.move(tmp_file_path, target_path)
            print(f"Java downloaded successfully to {target_path}")

            with zipfile.ZipFile(target_path, 'r') as zip_ref:
                zip_ref.extractall(java_dir)
            os.remove(target_path)

            print(f"Java extracted successfully to {java_dir}")

            return True
        except Exception as e:
            print(f"Error downloading and extracting Java: {e}")
            return False

    is_64bit = os.environ.get("PROCESSOR_ARCHITECTURE", "").endswith("64")
    if is_64bit:
        java_url = "https://api.adoptium.net/v3/binary/latest/8/ga/windows/x64/jre/hotspot/normal/eclipse"
    else:
        java_url = "https://api.adoptium.net/v3/binary/latest/8/ga/windows/x86/jre/hotspot/normal/eclipse"
    java_dir = os.path.join(os.getenv("APPDATA"), ".foxford", "java")

    if not check_java_version(java_dir):
        return download_java(java_url, java_dir)
    else:
        return True


if __name__ == "__main__":
    check_and_download_java()
