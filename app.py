import tkinter as tk
from tkinter import filedialog, messagebox
import pynbs
import zlib
import base64
import json
import requests

data_text = None
result_url = None

def get_direct_download_link(url: str) -> str:
    if url.startswith("http://tmpfiles.org/"):
        return url.replace("http://tmpfiles.org/", "http://tmpfiles.org/dl/")
    elif url.startswith("https://tmpfiles.org/"):
        return url.replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")
    return url

def toModule(base64_str):
    return """{"handlers":[{"type":"function","position":0,"operations":[{"action":"set_variable_create_list","values":[{"name":"values","value":{"type":"array","values":[{},{},{},{},{},{},{},{},{},{},{"type":"item","item":"{count:1,components:{\\"minecraft:custom_data\\":{PublicBukkitValues:{\\"justmc:template\\":%DATA%}}},id:\\"minecraft:ender_chest\\"}"},{},{},{},{},{},{},{},{},{},{}]}},{"name":"variable","value":{}}]}],"values":[],"name":""}]}""".replace(
        "%DATA%", f"[B;{','.join(str(ch)+'b' for ch in base64_str.encode())}]"
    )

def process_nbs_file(filepath):
    try:
        song = pynbs.read(filepath)
        notes = []
        prev_tick = -1
        tempo = song.header.tempo
        notes.append(tempo)

        for note in sorted(song.notes, key=lambda x: x.tick):
            tick, instrument, velocity, pitch = note.tick, note.instrument, note.velocity, note.key
            while tick > prev_tick + 1:
                notes.append([])
                prev_tick += 1
            if tick > prev_tick:
                notes.append([[tick, instrument, velocity, pitch]])
                prev_tick = tick
            else:
                notes[-1].append([tick, instrument, velocity, pitch])

        compressed = zlib.compress(json.dumps(notes).encode("utf-8"))
        return toModule(base64.b64encode(compressed).decode("utf-8"))

    except Exception as e:
        return f"Ошибка: {e}"

def upload_to_tmpfiles(content: str):
    try:
        files = {'file': ('result.json', content.encode('utf-8'))}
        response = requests.post('https://tmpfiles.org/api/v1/upload', files=files)
        response.raise_for_status()
        data = response.json()
        if data.get('status') == 'success':
            return get_direct_download_link(data['data']['url'])
    except Exception as e:
        print("Ошибка загрузки:", e)
    return None

def load_file():
    global result_url
    filepath = filedialog.askopenfilename(filetypes=[("Note Block Studio", "*.nbs")])
    if not filepath:
        return

    result = process_nbs_file(filepath)
    if result.startswith("Ошибка"):
        result_url = None
        preview_label.config(text="")
        command_entry.delete(0, tk.END)
        messagebox.showerror("Ошибка", result)
        return

    url = upload_to_tmpfiles(result)
    if not url:
        result_url = None
        preview_label.config(text="")
        command_entry.delete(0, tk.END)
        messagebox.showerror("Ошибка", "Не удалось загрузить файл.")
        return

    result_url = url
    preview_label.config(text=f"Ссылка: {url}")
    command_entry.delete(0, tk.END)
    command_entry.insert(0, f"/module loadUrl {url}")

def copy_result():
    command = command_entry.get()
    if command:
        root.clipboard_clear()
        root.clipboard_append(command)
    else:
        messagebox.showwarning("Нет команды", "Сначала выберите и загрузите файл.")

# GUI
root = tk.Tk()
root.title("NBS2JMC")
root.geometry("300x250")
root.resizable(False, False)

file_frame = tk.Frame(root)
file_frame.pack(pady=10)

tk.Label(file_frame, text="Выберите файл").grid(row=0, column=0, padx=5)
tk.Button(file_frame, text="Обзор", command=load_file).grid(row=0, column=1)

preview_label = tk.Label(root, text="", wraplength=280, justify=tk.LEFT)
preview_label.pack(padx=10, pady=5)

command_entry = tk.Entry(root, width=40)
command_entry.pack(pady=5)

tk.Button(root, text="Скопировать команду", command=copy_result).pack(pady=10)

root.mainloop()