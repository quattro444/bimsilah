import asyncio
import websockets

async def listen(ws):
    async for msg in ws:
        print(f"\n{msg}\n> ", end="")

async def main():
    uri = input("Inserisci URL del server (es. wss://nome-app.onrender.com): ")
    async with websockets.connect(uri) as ws:
        asyncio.create_task(listen(ws))

        while True:
            msg = input("> ")
            if msg.lower() == "exit":
                await ws.send("exit")
                break
            await ws.send(msg)

if __name__ == "__main__":
    asyncio.run(main())
