import socket
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext
import os
from datetime import datetime
import platform
import ctypes
from PIL import Image, ImageTk
import mimetypes

root = tk.Tk()
root.title("Glass Chat 💬")
root.geometry("520x600")
root.configure(bg="#101010")
root.resizable(False, False)

if platform.system() == "Darwin":
    root.wm_attributes("-transparent", True)
    root.attributes('-alpha', 0.9)
elif platform.system() == "Windows":
    HWND = ctypes.windll.user32.GetParent(root.winfo_id())
    ctypes.windll.dwmapi.DwmEnableBlurBehindWindow(HWND, ctypes.c_int(1))

font_normal = ("SF Pro Display", 12)
font_bold = ("SF Pro Display", 13, "bold")
accent_color = "#9FE2BF"

top_frame = tk.Frame(root, bg="#181818", height=60, bd=0, highlightthickness=0)
top_frame.pack(fill=tk.X)

tk.Label(top_frame, text="👤 Имя:", bg="#181818", fg="white", font=font_normal).pack(side=tk.LEFT, padx=(10, 3))
entry_name = tk.Entry(top_frame, width=12, font=font_normal, relief=tk.FLAT, bg="#222", fg="white", insertbackground="white")
entry_name.insert(0, "user")
entry_name.pack(side=tk.LEFT, padx=(0, 10))

tk.Label(top_frame, text="🌐 IP:", bg="#181818", fg="white", font=font_normal).pack(side=tk.LEFT)
entry_ip = tk.Entry(top_frame, width=14, font=font_normal, relief=tk.FLAT, bg="#222", fg="white", insertbackground="white")
entry_ip.insert(0, "localhost")
entry_ip.pack(side=tk.LEFT, padx=(0, 10))

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def connect_to_server():
    global sock, receive_thread
    server_ip = entry_ip.get().strip()
    username = entry_name.get().strip()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((server_ip, 12345))
        sock.send(username.encode('utf-8'))
        log_message("✅ Подключено к серверу.")
        receive_thread = threading.Thread(target=receive_messages, daemon=True)
        receive_thread.start()
    except Exception as e:
        log_message(f"❌ Ошибка подключения: {e}")

btn_connect = tk.Button(top_frame, text="🔌 Подключиться", command=connect_to_server, bg=accent_color, fg="black", font=font_bold, relief=tk.FLAT)
btn_connect.pack(side=tk.RIGHT, padx=10, pady=10)

chat_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg="#141414", fg="white", font=font_normal, relief=tk.FLAT, state=tk.DISABLED)
chat_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

_image_refs = []

bottom_frame = tk.Frame(root, bg="#181818", height=60)
bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

entry_message = tk.Entry(bottom_frame, font=font_normal, bg="#222", fg="white", insertbackground="white", relief=tk.FLAT)
entry_message.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
entry_message.bind("<Return>", lambda event: send_message())  # отправка по Enter

def send_message():
    msg = entry_message.get()
    if not msg:
        return
    try:
        sock.send(msg.encode('utf-8'))
        log_message(f"🧑‍💻 Вы: {msg}")
        entry_message.delete(0, tk.END)
    except Exception as e:
        log_message(f"⚠️ Ошибка отправки: {e}")

btn_send = tk.Button(bottom_frame, text="📨", command=send_message, bg=accent_color, fg="black", font=("Arial", 12, "bold"), relief=tk.FLAT, width=5)
btn_send.pack(side=tk.RIGHT, padx=10, pady=10)

def send_file():
    file_path = filedialog.askopenfilename()
    if not file_path:
        return

    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        data = f.read()

    try:
        header = f"/file {filename}|{len(data)}\n".encode("utf-8")
        sock.sendall(header)
        sock.sendall(data)
        log_message(f"📁 Файл {filename} отправлен ({len(data)} байт).")
    except Exception as e:
        log_message(f"⚠️ Ошибка при отправке файла: {e}")

btn_file = tk.Button(bottom_frame, text="📎", command=send_file, bg="#222", fg="white", relief=tk.FLAT, width=4)
btn_file.pack(side=tk.RIGHT, pady=10)

def receive_messages():
    buffer = b""
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break

            buffer += chunk

            while buffer.startswith(b"/file "):
                if b"\n" not in buffer:
                    break

                header, buffer = buffer.split(b"\n", 1)
                try:
                    header_text = header.decode("utf-8")[6:]
                    filename, size = header_text.split("|")
                    size = int(size)
                except Exception as e:
                    log_message(f"⚠️ Неправильный заголовок файла: {e}")
                    buffer = b""
                    break

                while len(buffer) < size:
                    more = sock.recv(4096)
                    if not more:
                        break
                    buffer += more

                filedata = buffer[:size]
                buffer = buffer[size:]

                save_path = os.path.join(DOWNLOAD_DIR, filename)
                try:
                    with open(save_path, "wb") as f:
                        f.write(filedata)
                except Exception as e:
                    log_message(f"⚠️ Ошибка сохранения файла: {e}")
                    continue

                filetype, _ = mimetypes.guess_type(save_path)
                if filetype and filetype.startswith("image"):
                    try:
                        img = Image.open(save_path)
                        img.thumbnail((200, 200))
                        tk_img = ImageTk.PhotoImage(img)
                        _image_refs.append(tk_img)

                        chat_box.config(state=tk.NORMAL)
                        timestamp = datetime.now().strftime("%H:%M")
                        chat_box.insert(tk.END, f"[{timestamp}] 🖼 {filename}\n")
                        chat_box.image_create(tk.END, image=tk_img)
                        chat_box.insert(tk.END, "\n")
                        chat_box.config(state=tk.DISABLED)
                        chat_box.see(tk.END)
                    except Exception as e:
                        log_message(f"⚠️ Ошибка отображения изображения: {e}")
                else:
                    log_message(f"📥 Файл сохранён: {save_path}")

            try:
                if buffer:
                    msg = buffer.decode("utf-8")
                    buffer = b""
                    log_message(msg)
            except Exception:
                pass

        except Exception:
            break

def log_message(text):
    chat_box.config(state=tk.NORMAL)
    timestamp = datetime.now().strftime("%H:%M")
    chat_box.insert(tk.END, f"[{timestamp}] {text}\n")
    chat_box.config(state=tk.DISABLED)
    chat_box.see(tk.END)

root.mainloop()