import aiohttp
import asyncio
import collections
import json
import logging
import sys
import time

from typing import List, Tuple

from messages import Message

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('testname.log')
c_handler.setLevel(logging.DEBUG)
f_handler.setLevel(logging.INFO)

c_format = logging.Formatter('%(message)s')
f_format = logging.Formatter('%(asctime)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

logger.addHandler(c_handler)
logger.addHandler(f_handler)


herd = {
    'Bailey': 17800,
    'Bona': 17801,
    'Campbell': 17802,
    'Clark': 17803,
    'Jaquez': 17804,
}

ipaddr='127.0.0.1'

USAGE = (
    f"Usage {sys.argv[0]} [srvname]"
)

clients = {}

def parse(args: List[str]) -> Tuple[str, int]:
    arguments = collections.deque(args)
    name=None
    while arguments:
        current = arguments.popleft()
        if name is None:
            if current in ["-h", "--help"]:
                print(USAGE)
                sys.exit(0)
            else:
                name = current
        else:
            print(USAGE)
            sys.exit(0)
    try:
        port = herd[name]
    except:
        print(f"\"{name}\" not a valid server.")
        sys.exit(0)
    return name, port

def parse_iamat():
    pass

TYPE = {
    'IAMAT': None,
    'WHATISAT': None,
    # 'IAM': None,
}

async def handle_echo(reader, writer):
    # Read info from sender
    data = await reader.read(100) # Want this to be as many as needed
    message = data.decode()
    addr = writer.get_extra_info('peername')
    logger.info(f"Received {message} from {addr}")

    # Parse the message. If we have a client 
    msg = Message(message, time.time())
    resp = msg.client_response('Bailey')

    # Reply to sender
    logger.info(f"Send: {resp!r}")
    writer.write(resp.encode())
    await writer.drain()

    logger.debug("Close the connection")
    writer.close()
    await writer.wait_closed()

async def main():
    fname, port = parse(sys.argv[1:])
    if not fname:
        raise SystemExit(USAGE)
    logger.info(f'Starting {fname} on port {port}')
    
    server = await asyncio.start_server(
        handle_echo, ipaddr, port=port)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logger.debug(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

# async def main():
#     async with aiohttp.ClientSession() as session:
#         async with session.get('http://httpbin.org/get') as resp:
#             print(resp.status)
#             print(await resp.text())

if __name__=='__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info(f"Keyboard Interrupt. Shutting down.\n")
        sys.exit(0)