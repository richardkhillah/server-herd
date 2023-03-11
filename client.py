from time import time, strftime

import asyncio
import sys

ipaddr = '127.0.0.1'

herd = {
    'Bailey': 17800,
    'Bona': 17801,
    'Campbell': 17802,
    'Clark': 17803,
    'Jaquez': 17804,
}

def iamat(host, coord, t=None):
    if t is None:
        t = time()
    formatted = f"IAMAT {host} {coord} {t}"
    return formatted

def whatsat(host, radius, page):
    formatted = f"WHATISAT {host} {radius} {page}"
    return formatted

async def tcp_echo_client(message, port):
    reader, writer = await asyncio.open_connection(
        ipaddr, port)

    print(f'Send: {message!r}')
    writer.write(message.encode())
    await writer.drain()

    data = await reader.read(100)
    print(f'Received: {data.decode()!r}')

    print('Close the connection')
    writer.close()
    await writer.wait_closed()

if __name__ == '__main__':
    h, c, t = 'kiwi.cs.ucla.edu', '+34.068930-118.445127', '1621464827.959498503'
    h2, c2, t2 = 'plum.cs.ucla.edu', '+34.068930-118.445127', '1621464827.959498503'
    r, p = 10, 5
    try:
        asyncio.run(tcp_echo_client(iamat(h, c), herd['Bailey']))
        asyncio.run(tcp_echo_client(whatsat(h, r, p), herd['Bailey']))
        asyncio.run(tcp_echo_client(whatsat(h2, r, p), herd['Bailey']))
    except ConnectionRefusedError as cre:
        print("Connection Refused")
        print(cre)
        sys.exit(-1)