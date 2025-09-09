import asyncio
import websockets
import json
import os

USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"

# === Utility per file ===
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
clients = {}  # {websocket: email}


async def register(ws):
    await ws.send("Inserisci email:")
    email = await ws.recv()
    if email in users:
        await ws.send("⚠️ Email già registrata.")
        return None

    await ws.send("Inserisci password:")
    password = await ws.recv()

    users[email] = {"password": password}
    save_data(USERS_FILE, users)
    messages[email] = []
    save_data(MESSAGES_FILE, messages)

    await ws.send("✅ Registrazione completata!")
    return email


async def login(ws):
    await ws.send("Email:")
    email = await ws.recv()
    await ws.send("Password:")
    password = await ws.recv()

    if email not in users or users[email]["password"] != password:
        await ws.send("❌ Credenziali errate.")
        return None

    await ws.send("✅ Login effettuato!")
    return email


async def broadcast(message, sender=None):
    for client in list(clients.keys()):
        if client != sender:
            try:
                await client.send(message)
            except:
                pass


async def handler(ws):
    await ws.send("Benvenuto! Vuoi fare [login/registrati]?")
    choice = await ws.recv()

    email = None
    if choice == "registrati":
        email = await register(ws)
    elif choice == "login":
        email = await login(ws)
    else:
        await ws.send("❌ Scelta non valida.")
        return

    if not email:
        return

    clients[ws] = email
    await broadcast(f"🔵 {email} si è connesso.", ws)

    # Messaggi non letti
    if messages.get(email):
        await ws.send("📥 I tuoi messaggi non letti:")
        for msg in messages[email]:
            await ws.send(f"{msg['da']}: {msg['testo']}")
        messages[email] = []
        save_data(MESSAGES_FILE, messages)

    try:
        async for msg in ws:
            if msg.lower() == "exit":
                break
            await broadcast(f"{email}: {msg}", ws)
    except:
        pass
    finally:
        if ws in clients:
            await broadcast(f"🔴 {clients[ws]} si è disconnesso.", ws)
            del clients[ws]


async def main():
    port = int(os.environ.get("PORT", 10000))  # Render userà questa porta
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"[SERVER AVVIATO SU PORTA {port}]")
        await asyncio.Future()  # per tenere il server attivo


if __name__ == "__main__":
    asyncio.run(main())
