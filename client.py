import asyncio

def iamat(host, coord, time):
    formatted = f"IAMAT {host} {coord} {time}"
    return formatted

def whatsat():
    pass

async def tcp_echo_client(message):
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', 8888)

    print(f'Send: {message!r}')
    writer.write(message.encode())
    await writer.drain()

    data = await reader.read(100)
    print(f'Received: {data.decode()!r}')

    print('Close the connection')
    writer.close()
    await writer.wait_closed()

if __name__ == '__main__':
    # asyncio.run(tcp_echo_client('Hello World!'))
    h, c, t = 'kiwi.cs.ucla.edu', '+34.068930-118.445127', '1621464827.959498503'
    asyncio.run(tcp_echo_client(iamat(h, c, t)))