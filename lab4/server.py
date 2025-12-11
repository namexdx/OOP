import os
import threading
import logging
import socket
from flask import Flask, render_template
from flask_socketio import SocketIO

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

clients = {} 
os.makedirs("uploaded_files", exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return render_template('test.html')

@socketio.on('message')
def handle_web_message(msg):
    logging.info(f"🌐 WebClient: {msg}")
    if isinstance(msg, dict) and 'name' in msg and 'text' in msg:
        broadcast_to_all(msg)
    else:
        logging.error("Получено сообщение с неправильной структурой: %s", msg)

def tcp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", 12345))
    sock.listen(5)
    logging.info("TCP сервер запущен на порту 12345")

    while True:
        client, addr = sock.accept()
        threading.Thread(target=handle_tcp_client, args=(client, addr), daemon=True).start()

def handle_tcp_client(client_socket, addr):
    try:
        username = client_socket.recv(1024).decode("utf-8")
    except Exception as e:
        logging.error("Не удалось прочитать имя клиента: %s", e)
        client_socket.close()
        return

    logging.info(f"{username} присоединился к чату.")
    clients[client_socket] = username
    broadcast_to_all({"name": "Система", "text": f"🟢 {username} присоединился к чату."})

    buffer = b""
    try:
        while True:
            chunk = client_socket.recv(4096)
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
                    logging.error("Некорректный заголовок файла: %s", e)
                    buffer = b""
                    break

                while len(buffer) < size:
                    more = client_socket.recv(4096)
                    if not more:
                        break
                    buffer += more

                filedata = buffer[:size]
                buffer = buffer[size:]

                filepath = os.path.join("uploaded_files", filename)
                try:
                    with open(filepath, "wb") as f:
                        f.write(filedata)
                except Exception as e:
                    logging.error("Ошибка сохранения файла на сервере: %s", e)
                    continue

                logging.info(f"📁 {username} загрузил файл {filename} ({size} bytes)")

                header_bytes = f"/file {filename}|{size}\n".encode("utf-8")
                dead = []
                for c in list(clients.keys()):
                    try:
                        c.sendall(header_bytes)
                        sent = 0
                        CHUNK = 4096
                        while sent < size:
                            tosend = filedata[sent:sent+CHUNK]
                            if not tosend:
                                break
                            c.sendall(tosend)
                            sent += len(tosend)
                    except Exception:
                        dead.append(c)
                for d in dead:
                    try:
                        del clients[d]
                    except:
                        pass

                socketio.emit('message', {"name": username, "text": f"📎 Отправил файл: {filename}"})

            try:
                if buffer:
                    message = buffer.decode("utf-8")
                    buffer = b""
                    logging.info(f"{username}: {message}")
                    broadcast_to_all({"name": username, "text": message})
            except Exception:
                pass

    except Exception as e:
        logging.error(f"Ошибка при обработке клиента: {e}")

    finally:
        try:
            client_socket.close()
        except:
            pass
        if client_socket in clients:
            del clients[client_socket]
        broadcast_to_all({"name": "Система", "text": f"🔴 {username} отключился."})

def broadcast_to_all(msg):
    text = f"{msg['name']}: {msg['text']}"
    for c in list(clients.keys()):
        try:
            c.sendall(text.encode("utf-8"))
        except Exception:
            try:
                del clients[c]
            except:
                pass
    socketio.emit('message', msg)

if __name__ == "__main__":
    threading.Thread(target=tcp_server, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=8000)