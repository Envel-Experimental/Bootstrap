# launcher_binary.py
import os
from zipfile import ZipFile

from java_launcher import JavaLauncher


class LauncherBinary:
    def __init__(self, path):
        self.path = path

    def test_jar(self):
        try:
            with ZipFile(self.path, 'r') as zip_file:
                return len(zip_file.infolist()) > 0
        except Exception:
            return False

    def delete(self):
        os.remove(self.path)

    def create_launcher(self, args):
        return JavaLauncher(args, self.path)
