import aiohttp
import asyncio
import collections
import logging
import sys
import time

from typing import List, Tuple

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

class Message:
    def __init__(self, message, received_time=None):
        self.type=None
        self.skew=None
        self.addr=None
        self.lon=None
        self.lat=None
        self.radius=None
        self.pagination=None
        self.client_time=None
        self._message=message
        if message.startswith(('IAMAT', 'WHATISAT')):
            m = message.split()
            type=m[0]
            if type == 'IAMAT' and len(m) == 4:
                # IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 1621464827.959498503
                self.type = 'IAMAT'
                self.addr = m[1]
                coords = self.crude_coord_split(m[2])
                self.lat = (coords[0], coords[1]) # ['+/-', 'floatstring']
                self.lon = (coords[2], coords[3]) # ['+/-', 'floatstring']
                self.client_time = m[3]
                self.skew = received_time - float(self.client_time)

            elif type == 'WHATISAT' and len(m) == 4:
                #TODO: Implement
                pass
            
    def _body(self):
        b = self.addr
        c = "".join([*self.lon, *self.lat]) if self.type == 'IAMAT' else self.radius
        d = self.client_time if self.type == 'IAMAT' else self.pagination
        return f'{b} {c} {d}'
    
    def __str__(self):
        a = self.type
        b = self._body()
        return f"{a} {b}"
    
    def response(self, at, payload=None):
        if self.type not in ('IAMAT', 'WHATISAT'):
            return f"? {self._message}"
        return f"AT {at} {self.skew} {self._body()}"

    def crude_coord_split(self, coordstr):
        # s = '+34.068930-118.445127'
        ret = []
        temp=""
        for i in coordstr:
            if i in ['+', '-']:
                if temp != "":
                    ret.append(temp)
                ret.append(i)
                temp=""
                continue
            temp += i
        ret.append(temp)
        # FIX ME Ensure coordinates have the above form
        return ret

async def handle_echo(reader, writer):
    # Read info from sender
    data = await reader.read(100) # Want this to be as many as needed
    message = data.decode()
    addr = writer.get_extra_info('peername')
    logger.info(f"Received {message} from {addr}")

    resp = Message(message, time.time()).response('Bailey', None)

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