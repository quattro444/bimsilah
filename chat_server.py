import socket
import threading
import json
import os

USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"

# === Utility per salvataggio dati ===
def load_data(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return default

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

users = load_data(USERS_FILE, {})
messages = load_data(MESSAGES_FILE, {})

clients = {}  # {conn: email}


# === Gestione client ===
def handle_client(conn, addr):
    try:
        conn.send("Benvenuto! Vuoi fare [login/registrati]? ".encode("utf-8"))
        choice = conn.recv(1024).decode("utf-8").strip()

        email = None
        if choice == "registrati":
            conn.send("Inserisci email: ".encode("utf-8"))
            email = conn.recv(1024).decode("utf-8").strip()
            if email in users:
                conn.send("⚠️ Email già registrata.\n".encode("utf-8"))
                conn.close()
                return
            conn.send("Inserisci password: ".encode("utf-8"))
            password = conn.recv(1024).decode("utf-8").strip()
            users[email] = {"password": password}
            save_data(USERS_FILE, users)
            messages[email] = []
            save_data(MESSAGES_FILE, messages)
            conn.send("✅ Registrazione completata!\n".encode("utf-8"))

        elif choice == "login":
            conn.send("Email: ".encode("utf-8"))
            email = conn.recv(1024).decode("utf-8").strip()
            conn.send("Password: ".encode("utf-8"))
            password = conn.recv(1024).decode("utf-8").strip()
            if email not in users or users[email]["password"] != password:
                conn.send("❌ Credenziali errate.\n".encode("utf-8"))
                conn.close()
                return
            conn.send("✅ Login effettuato!\n".encode("utf-8"))

        else:
            conn.send("❌ Scelta non valida.\n".encode("utf-8"))
            conn.close()
            return

        # Salviamo il client
        clients[conn] = email
        broadcast(f"🔵 {email} si è connesso alla chat.", conn)

        # Mostriamo messaggi non letti
        if email in messages and messages[email]:
            conn.send("📥 I tuoi messaggi non letti:\n".encode("utf-8"))
            for msg in messages[email]:
                conn.send(f"{msg['da']}: {msg['testo']}\n".encode("utf-8"))
            messages[email] = []
            save_data(MESSAGES_FILE, messages)

        # Ciclo ricezione messaggi
        while True:
            msg = conn.recv(1024).decode("utf-8")
            if not msg:
                break
            if msg.lower() == "exit":
                break
            # Inoltra a tutti
            broadcast(f"{email}: {msg}", conn)

    except:
        pass
    finally:
        if conn in clients:
            broadcast(f"🔴 {clients[conn]} si è disconnesso.", conn)
            del clients[conn]
        conn.close()


def broadcast(msg, sender_conn=None):
    for client in list(clients.keys()):
        try:
            if client != sender_conn:
                client.send((msg + "\n").encode("utf-8"))
        except:
            client.close()
            del clients[client]


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 5555))  # ascolta su porta 5555
    server.listen()
    print("[SERVER IN ASCOLTO SU PORTA 5555]")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


if __name__ == "__main__":
    main()
