import os
import subprocess


class JavaError(Exception):
    pass


def find_java_executable():
    java_dir = os.path.join(os.getenv("APPDATA"), ".foxford", "java")
    if os.path.isdir(java_dir):
        for root, dirs, files in os.walk(java_dir):
            for file in files:
                if file == "java" or file == "java.exe":
                    return os.path.join(root, file)
    return None


class JavaLauncher:
    def __init__(self, args, jar_path):
        self.args = args
        self.jar_path = jar_path

    def launch(self):
        java_executable_path = find_java_executable()
        if java_executable_path:
            java_command = java_executable_path
            print(f"Using Java found in {java_executable_path}.")
        else:
            try:
                subprocess.check_call(["java", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
                java_command = "java"
                print("Using system Java.")
            except subprocess.CalledProcessError:
                print("Failed to find Java.")
                return

        cmd = [java_command, "-jar", self.jar_path] + self.args
        try:
            subprocess.Popen(cmd, shell=False, start_new_session=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return
        except Exception as e:
            raise JavaError(f"Failed to launch Java process: {e}")
        return
