import tkinter as tk
from tkinter import filedialog, messagebox
import pynbs
import zlib
import base64
import json
import requests
import io

result_url = None
preview_lines = 3

def get_direct_download_link(url: str) -> str:
    # Пример:
    # "http://tmpfiles.org/1592738/result.json" -> "http://tmpfiles.org/dl/1592738/result.json"
    if url.startswith("http://tmpfiles.org/"):
        return url.replace("http://tmpfiles.org/", "http://tmpfiles.org/dl/")
    elif url.startswith("https://tmpfiles.org/"):
        return url.replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")
    else:
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
            tick = note.tick
            instrument = note.instrument
            velocity = note.velocity
            pitch = note.key

            while tick > prev_tick + 1:
                notes.append([])
                prev_tick += 1

            if tick > prev_tick:
                notes.append([[tick, instrument, velocity, pitch]])
                prev_tick = tick
            else:
                notes[-1].append([tick, instrument, velocity, pitch])

        notes_json = json.dumps(notes)
        compressed = zlib.compress(notes_json.encode("utf-8"))
        base64_notes = base64.b64encode(compressed).decode("utf-8")

        return toModule(base64_notes)
    except Exception as e:
        return f"Ошибка: {e}"

def upload_to_tmpfiles(content: str):
    try:
        files = {
            'file': ('result.json', content.encode('utf-8'))
        }
        response = requests.post('https://tmpfiles.org/api/v1/upload', files=files)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 'success' and 'data' in data and 'url' in data['data']:
            url = data['data']['url']
            direct_url = get_direct_download_link(url)
            return direct_url
        else:
            print("Ошибка в ответе API:", data)
            return None
    except Exception as e:
        print("Исключение при загрузке:", e)
        return None

def load_file():
    global result_url
    filepath = filedialog.askopenfilename(filetypes=[("Note Block Studio Files", "*.nbs")])
    if not filepath:
        return

    result = process_nbs_file(filepath)
    if result.startswith("Ошибка"):
        result_url = None
        preview_box.delete(1.0, tk.END)
        messagebox.showerror("Ошибка", result)
        return

    url = upload_to_tmpfiles(result)
    if not url:
        messagebox.showerror("Ошибка", "Не удалось загрузить результат на tmpfiles.org")
        result_url = None
        preview_box.delete(1.0, tk.END)
        return

    result_url = url
    preview_box.delete(1.0, tk.END)
    preview_box.insert(tk.END, f"Файл загружен и доступен для загрузки в течении 60 минут.\nСсылка {url}")

    messagebox.showinfo("Успешно", "Файл обработан и загружен. Ссылка доступна ниже.")

def copy_result():
    if result_url:
        root.clipboard_clear()
        root.clipboard_append(result_url)
        messagebox.showinfo("Скопировано", "Ссылка на результат скопирована в буфер обмена.")
    else:
        messagebox.showwarning("Нет данных", "Сначала загрузите и загрузите файл.")

root = tk.Tk()
root.title("NBS2JMC")
root.geometry("700x400")

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

load_btn = tk.Button(btn_frame, text="Загрузить .nbs", command=load_file, width=20)
load_btn.pack(side=tk.LEFT, padx=5)

copy_btn = tk.Button(btn_frame, text="Скопировать ссылку", command=copy_result, width=20)
copy_btn.pack(side=tk.LEFT, padx=5)

preview_box = tk.Text(root, height=15, wrap=tk.WORD)
preview_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

root.mainloop()
