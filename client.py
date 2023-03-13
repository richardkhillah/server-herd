from time import time, strftime

import asyncio
import json
import sys

ipaddr = '127.0.0.1'

herd = {
    'Bailey': 17800,
    'Bona': 17801,
    'Campbell': 17802,
    'Clark': 17803,
    'Jaquez': 17804,
}

def iamat(host, coord, t=None, skew=None):
    if t is None:
        t = time()
    if skew is not None:
        t + skew
        print(t+skew)
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
    writer.write_eof()

    if 'WHATISAT' in message:
        while not reader.at_eof():
            data = await reader.readline()
            if decoded := data.decode():
                if decoded.startswith('AT'):
                    print(f"decoded: {decoded}")
                elif not decoded.startswith('?'):
                    json_data = json.loads(decoded)
                    print( f'{len(json_data["results"])=}')
                elif decoded.startswith('?'):
                    print(decoded)
    else:
        data = await reader.read()
        decoded_data = data.decode()
        print(f'Received: {decoded_data!r}')

    print('Close the connection')
    writer.close()
    await writer.wait_closed()

async def time_after(n):
    print(f'sleep for {n=}')
    await asyncio.sleep(n)
    print(f'wokeup')
    return time()

async def main():
    hosts = ['kiwi.cs.ucla.edu', 'plum.cs.ucla.edu', 'watermelon.cs.ucla.edu']
    coordinates = ['+34.068930-118.445127', '+55.555555-666.666666', '+77.777777-888.888888']
    times = ['']

    h, c, t = 'kiwi.cs.ucla.edu', '+34.068930-118.445127', '1621464827.959498503'
    h2, c2, t2 = 'plum.cs.ucla.edu', '+77.770077-999.99999', time()
    r, p = 10, 5
    try:
        # t = await asyncio.gather(
        #     *(time_after(i) for i in range(6))
        # )
        # t = await time_after(5)
        r = await asyncio.gather(
            tcp_echo_client(iamat(h, c), herd['Bailey']),
            tcp_echo_client(whatsat(h, r, p), herd['Bailey']),
            # tcp_echo_client(whatsat(h, r, 3), herd['Bailey']),
            # tcp_echo_client(whatsat(h, r, 6), herd['Bailey']),
            # tcp_echo_client(whatsat(h2, r, p), herd['Bailey']),
            # tcp_echo_client(iamat(h2, c2, t=t2, skew=1000000000), herd['Bailey']),
            # tcp_echo_client(iamat(h2, c2), herd['Bailey']),
            # tcp_echo_client(iamat(h2, c), herd['Bailey']),
            # tcp_echo_client(whatsat(h, r, p), herd['Campbell']),
            # tcp_echo_client(whatsat(h, r, 3), herd['Campbell'])
        )

        print(f'{t=}')
        print(f'{r=}')



    except ConnectionRefusedError as cre:
        print("Connection Refused")
        print(cre)
        sys.exit(-1)

if __name__ == '__main__':
    asyncio.run(main())