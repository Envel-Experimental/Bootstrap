import os
import shutil
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import requests
from requests import RequestException
from launcher_binary import LauncherBinary
from version_check import check_and_download_java
from queue import Queue

class BootstrapperGUI:
    def __init__(self, update_url, app_name, org_name, portable, bootstrap_args):
        self.update_url = update_url
        self.app_name = app_name
        self.org_name = org_name
        self.portable = portable
        self.bootstrap_args = bootstrap_args

        self.base_dir = os.path.join(os.getenv("APPDATA"), ".foxford")
        self.jar_dir = os.path.join(self.base_dir, "jar")
        self.java_dir = os.path.join(self.base_dir, "java")
        self.minecraft_dir = os.path.join(self.base_dir, "minecraft")

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        window_width = 350
        window_height = 120
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_coordinate = (screen_width - window_width) / 2
        y_coordinate = (screen_height - window_height) / 2
        self.root.geometry(f"{window_width}x{window_height}+{int(x_coordinate)}+{int(y_coordinate)}")

        self.root.attributes("-alpha", 0.9)

        style = ttk.Style()
        style.theme_use('clam')

        style.layout("custom.Horizontal.TProgressbar",
                     [('custom.Horizontal.TProgressbar.trough', {'sticky': 'nswe', 'children':
                         [('custom.Horizontal.TProgressbar.pbar', {'side': 'left', 'sticky': 'ns'})]})])
        style.configure("custom.Horizontal.TProgressbar", troughcolor='white', bordercolor='white',
                        background='#f58427', thickness=20)

        self.background_frame = tk.Frame(self.root, bg="white")
        self.background_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.label_main = tk.Label(self.background_frame, text="Установка Фоксфорд в Minecraft",
                                   font=("Arial", 14, "bold"), fg="black", bg="white")
        self.label_main.pack(pady=(10, 5))

        self.label_status = tk.Label(self.background_frame, text="Инициализация...", font=("Arial", 10), fg="black",
                                     bg="white")
        self.label_status.pack()

        self.cancel_button = tk.Button(self.background_frame, text="Отменить", font=("Arial", 10), fg="gray",
                                       activeforeground="gray", bd=0, command=self.close_window)
        self.cancel_button.pack(pady=5)

        self.progress_bar = ttk.Progressbar(self.background_frame, orient="horizontal", mode="indeterminate",
                                            style="custom.Horizontal.TProgressbar")
        self.progress_bar.pack(side="bottom", fill="x")
        self.progress_bar.start()

        self.error_queue = Queue()

        threading.Thread(target=self.run).start()

    def run(self):
        try:
            os.makedirs(self.base_dir, exist_ok=True)
            os.makedirs(self.jar_dir, exist_ok=True)
            os.makedirs(self.java_dir, exist_ok=True)
        except OSError as e:
            self.error_queue.put(f"Ошибка создания каталогов: {e}")
            return

        try:
            os.environ["HOME"] = self.minecraft_dir
        except Exception as e:
            self.error_queue.put(f"Ошибка установки переменной среды HOME: {e}")
            return

        if not self.cleanup(self.jar_dir):
            self.error_queue.put("Ошибка при очистке!")
            return

        try:
            self.launch(self.jar_dir)
        except Exception as e:
            self.error_queue.put(f"Ошибка: {e}")

    def cleanup(self, jar_dir):
        try:
            for filename in os.listdir(jar_dir):
                filepath = os.path.join(jar_dir, filename)
                if filename.endswith(".tmp"):
                    os.remove(filepath)
            return True
        except Exception as e:
            self.error_queue.put(f"Ошибка при очистке: {e}")
            return False

    def close_window(self):
        self.root.quit()
        self.root.destroy()
        sys.exit()

    def launch(self, jar_dir):
        java_version = check_and_download_java()
        if not java_version:
            self.error_queue.put("Недопустимая версия Java: Необходима Java 8 или выше")
            return

        binaries = self.load_existing_binaries(jar_dir)
        if not binaries:
            new_binaries = self.download_binaries(jar_dir)
            if new_binaries:
                binaries = new_binaries
            else:
                self.error_queue.put("Не найдены исполняемые файлы загрузчика.")
                return

        working_binary = next((bin for bin in binaries if bin.test_jar()), None)
        if not working_binary:
            self.error_queue.put("Не найдены работающие исполняемые файлы загрузчика.")
            return

        for binary in binaries:
            if binary != working_binary:
                binary.delete()

        args = []
        if not self.portable:
            args.extend(["--dir", self.minecraft_dir])
        if self.portable:
            args.append("--portable")
        args.extend(["--bootstrap-version", "1"])
        args.extend(self.bootstrap_args)

        launcher = working_binary.create_launcher(args)
        launcher.launch()
        self.close_window()

    def load_existing_binaries(self, jar_dir):
        try:
            return [LauncherBinary(os.path.join(jar_dir, filename)) for filename in os.listdir(jar_dir)]
        except Exception:
            return []

    def download_binaries(self, jar_dir):
        try:
            update_meta = requests.get(self.update_url).json()
            self.label_status.config(text=f"Загрузка версии {update_meta['version']}...")
            self.root.update()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".jar") as tmp_file:
                response = requests.get(update_meta['url'], stream=True)
                shutil.copyfileobj(response.raw, tmp_file)
            target_name = os.path.join(jar_dir, os.path.basename(tmp_file.name))
            shutil.move(tmp_file.name, target_name)

            self.label_status.config(text=f"Скачано {os.path.basename(target_name)}")
            self.root.update()

            return [LauncherBinary(target_name)]
        except RequestException as e:
            self.error_queue.put(f"Не удалось загрузить новый загрузчик: {e}")
            return None

def main():
    bootstrap_settings = {
        "update_url": "https://bitbucket.org/Enlar/foxford.bitbucket.io/raw/master/latest.json",
        "app_name": "FoxFord",
        "org_name": "FoxFord Launcher"
    }
    bootstrap_args = []
    portable = os.path.exists("portable.txt")
    bootstrapper = BootstrapperGUI(**bootstrap_settings, portable=portable, bootstrap_args=bootstrap_args)
    bootstrapper.root.mainloop()

    while not bootstrapper.error_queue.empty():
        messagebox.showerror("Ошибка", bootstrapper.error_queue.get())

if __name__ == "__main__":
    main()