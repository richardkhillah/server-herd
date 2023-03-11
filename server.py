import aiohttp
import asyncio
import logging

logging.basicConfig(filename='testname.log', level=logging.INFO,
                             format='%(asctime)s - %(message)s')


async def handle_echo(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    addr = writer.get_extra_info('peername')

    logging.info(f"Received {message} from {addr}")

    print(f"Received {message!r} from {addr!r}")

    print(f"Send: {message!r}")
    writer.write(data)
    await writer.drain()

    print("Close the connection")
    writer.close()
    await writer.wait_closed()

async def main():
    server = await asyncio.start_server(
        handle_echo, '127.0.0.1', 8888)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

# async def main():
#     async with aiohttp.ClientSession() as session:
#         async with session.get('http://httpbin.org/get') as resp:
#             print(resp.status)
#             print(await resp.text())

if __name__=='__main__':
    asyncio.run(main())