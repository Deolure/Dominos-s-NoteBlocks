import tkinter as tk
from tkinter import filedialog, messagebox
import pynbs
import zlib
import base64
import json

result_data = None  # Полный текст
preview_lines = 5  # Кол-во строк предпросмотра

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

def load_file():
    global result_data
    filepath = filedialog.askopenfilename(filetypes=[("Note Block Studio Files", "*.nbs")])
    if not filepath:
        return

    result = process_nbs_file(filepath)
    if result.startswith("Ошибка"):
        result_data = None
        preview_box.delete(1.0, tk.END)
        messagebox.showerror("Ошибка", result)
    else:
        result_data = result
        # Обновить окно предпросмотра (только первые строки)
        preview_box.delete(1.0, tk.END)
        lines = result.splitlines()
        preview = "\n".join(lines[:preview_lines])
        preview_box.insert(tk.END, preview + ("\n..." if len(lines) > preview_lines else ""))
        messagebox.showinfo("Успешно", "Файл загружен. Предпросмотр обновлён.")

def copy_result():
    if result_data:
        root.clipboard_clear()
        root.clipboard_append(result_data)
        messagebox.showinfo("Скопировано", "Полный результат скопирован в буфер обмена.")
    else:
        messagebox.showwarning("Нет данных", "Сначала загрузите файл.")

# GUI
root = tk.Tk()
root.title("NBS в JustMC")
root.geometry("700x400")

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

load_btn = tk.Button(btn_frame, text="Загрузить .nbs", command=load_file, width=20)
load_btn.pack(side=tk.LEFT, padx=5)

copy_btn = tk.Button(btn_frame, text="Скопировать результат", command=copy_result, width=20)
copy_btn.pack(side=tk.LEFT, padx=5)

preview_box = tk.Text(root, height=15, wrap=tk.WORD)
preview_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

root.mainloop()
