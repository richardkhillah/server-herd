import aiohttp
import asyncio
import collections
import json
import logging
import sys
import time

# from typing import List, Tuple

import env
from request import Request
from record import Record, Position

logger = logging.getLogger(__name__)

use_dummy_api = True
use_my_herd = True

def init_logger(filename):
    logger.setLevel(logging.DEBUG)

    
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(filename+".log", mode="w")
    c_handler.setLevel(logging.DEBUG)
    f_handler.setLevel(logging.INFO)

    c_format = logging.Formatter('%(message)s')
    f_format = logging.Formatter('%(asctime)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

my_herd = {
    'Bailey': 17800,
    'Bona': 17801,
    'Campbell': 17802,
    'Clark': 17803,
    'Jaquez': 17804,
}

seas_herd = {
    'Bailey': 10000,
    'Bona': 10001,
    'Campbell': 10002,
    'Clark': 10003,
    'Jaquez': 10004,
}

# Change this to seas herd when runnin on seas
herd = seas_herd
if use_my_herd:
    herd = my_herd

graph = {
    'Bailey': ['Campbell', 'Bona'],
    'Bona': ['Clark', 'Campbell', 'Bailey'],
    'Campbell': ['Bailey', 'Bona', 'Jaquez'],
    'Clark': ['Jaquez', 'Bona'],
    'Jaquez': ['Clark', 'Campbell'],
}

# Clark talks with Jaquez and Bona.
# Campbell talks with everyone else but Clark.
# Bona talks with Bailey.

MYNAME=""

IPADDR='127.0.0.1'

USAGE = (
    f"Usage {sys.argv[0]} [srvname]"
)

class Server:
    def __init__(self, fname, ipaddr, port, neighbors):
        self.myname = fname
        self.ipaddr = ipaddr
        self.port = port
        self.neighbors = neighbors
        self.records = {}

    async def run(self):
        logger.info(f'Starting {self.myname} on port {self.port}')
        server = await asyncio.start_server(
            self.handle_echo, self.ipaddr, port=self.port)

        async with server:
            await server.serve_forever()

    def make_position(self, req):
        return Position(req.lat, req.lon, 
                        radius=req.radius, 
                        pagination=req.pagination, 
                        payload=req._payload)

    def make_record(self, req):
        return Record(
                req.addr,
                req.skew,
                req.client_time,
                self.make_position(req),
            )

    def get_or_create_client_record(self, req):
        try:
            rec = self.records[req.addr]
        except:
            rec = self.make_record(req)
        return rec

    async def process_request(self, request, rec):
        payload = None

        if request.is_whatsat() and rec.is_new():
            request.mark_invalid()

        if request.is_valid():
            if (request.is_at() or request.is_iamat()) and \
               (rec.is_new() or (rec.client_time < request.client_time)):
                self.records[rec.addr] = rec
                rec.mark_notnew()
                request.set_flood(True)

            elif request.is_whatsat():
                loc = rec.position.api_location
                rad = request.radius
                pag = request.pagination
                api_response = await api_call(loc, rad, pag)
                payload = json.dumps(api_response)

            else:
                # received duplicate or 
                request.mark_invalid()
        
        return payload

    async def handle_echo(self, reader, writer):
        # Read info from sender
        while not reader.at_eof():
            data = await reader.read() # Want this to be as many as needed
        
            message = data.decode()
            logger.info(f"Received {message}")

            # Parse the message. If we have a client 
            request = Request(message, time.time())
        
            # if reqest is valid, process, otherwise trap
            rec = self.get_or_create_client_record(request)
            
            # Handle the request information
            payload = await self.process_request(request, rec)
            
            # Respond to Client
            if not request.is_at():
                await self.respond_to_client(writer, request, rec, payload)

            # Propigate to neighbors
            if request.is_valid() and request.flood:
                await self.propagate(request)

    async def respond_to_client(self, writer, request, rec, payload):
        resp = request.response(self.myname, rec, payload=payload)
                
        # Reply to sender
        logger.info(f"Send: {resp}")
        writer.write(resp.encode())
        await writer.drain()

        logger.debug("Close the connection")
        writer.close()
        await writer.wait_closed()

    async def propagate(self, request: Request):
        request.mark_visited(self.myname)
        visited = request.get_visited()
        to_visit = [n for n in self.neighbors if n[0] not in visited]
        resp = request.flood_response(self.myname)
        for neighbor, port in to_visit:
            try:
                _, writer = await asyncio.open_connection(self.ipaddr, port)
                logger.info(f'Sent {neighbor}: {resp}')
                writer.write(resp.encode())
                await writer.drain()
                writer.write_eof()
                writer.close()
                await writer.wait_closed()
            except:
                logger.info(f"Unable to connect to {neighbor}")


async def dummy_api_call(location, radius, pagination):
    import aiofiles
    async with aiofiles.open('places_raw.json', mode='r') as rf:
        read_data = await rf.read()
    data = json.loads(read_data)
    data['results'] = data['results'][:pagination]
    return data

async def places_api_call(location, radius, pag):
    key = env.PLACES_API_KEY
    url=(
        f'https://maps.googleapis.com/maps/api/place/nearbysearch/json' +
        f'?location={location}' +
        f'&radius={radius}' +
        f'&key={key}'
    )
    ret = None
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.text()
            json_data = json.loads(data)
            json_data['results'] = json_data['results'][:pag]
            return json_data

api_call = places_api_call
if use_dummy_api:
    api_call = dummy_api_call

def parse(args):
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
        neighbor_names = graph[name]
    except:
        raise Exception(f"\"{name}\" not a valid server.")
    return name, port, neighbor_names

async def main():
    sname, port, neighbor_names = parse(sys.argv[1:])
    if not sname:
        raise SystemExit(USAGE)
    
    init_logger(sname)

    neighbors = set(zip(neighbor_names, [herd[n] for n in neighbor_names]))
    server = Server(sname, IPADDR, port, neighbors)
    
    await server.run()

if __name__=='__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info(f"Keyboard Interrupt. Shutting down.\n")
        sys.exit(0)