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

ipaddr='127.0.0.1'

USAGE = (
    f"Usage {sys.argv[0]} [srvname]"
)

records = {}

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
    except:
        raise Exception(f"\"{name}\" not a valid server.")
    return name, port

def make_position(req):
    return Position(req.lat, req.lon, 
                     radius=req.radius, 
                     pagination=req.pagination, 
                     payload=req._payload)

def make_record(req):
    return Record(
            req.addr,
            req.skew,
            req.client_time,
            make_position(req),
        )

def get_or_create_client_record(req):
    try:
        rec = records[req.addr]
    except:
        rec = make_record(req)
    return rec

async def process_request(request, rec):
    payload = None

    if request.is_whatsat() and rec.is_new():
        request.mark_invalid()

    if request.is_valid():
        if (request.is_at() or request.is_iamat()) and \
           (rec.is_new() or rec.client_time < request.client_time):
            rec.mark_notnew()
            records[rec.addr] = rec
            request.set_flood(True)

        # Existing Client Query
        elif request.is_whatsat():
            loc = rec.position.api_location
            rad = request.radius
            pag = request.pagination
            api_response = await api_call(loc, rad, pag)
            payload = json.dumps(api_response)

        else:
            # This should be unreachable
            request.mark_invalid()
    
    return payload

async def handle_echo(reader, writer):
    # Read info from sender
    while not reader.at_eof():
        data = await reader.read() # Want this to be as many as needed
    
        message = data.decode()
        logger.info(f"Received {message}")

        # Parse the message. If we have a client 
        request = Request(message, time.time())
    
        # if reqest is valid, process, otherwise trap
        rec = get_or_create_client_record(request)
        
        # Handle the request information
        payload = await process_request(request, rec)
           
        # Respond to Client
        if not request.is_at():
            await respond_to_client(writer, request, rec, payload)

        # Propigate to neighbors
        if request.is_valid() and request.flood:
            await propagate(request)

async def respond_to_client(writer, request, rec, payload):
    resp = request.response(MYNAME, rec, payload=payload)
            
    # Reply to sender
    logger.info(f"Send: {resp}")
    writer.write(resp.encode())
    await writer.drain()

    logger.debug("Close the connection")
    writer.close()
    await writer.wait_closed()

async def propagate(request: Request):
    request.mark_visited(MYNAME)
    visited = request.get_visited()
    to_visit = [x for x in graph[MYNAME] if x not in visited]
    resp = request.flood_response(MYNAME)
    for neighbor in to_visit:
        try:
            _, writer = await asyncio.open_connection(ipaddr, herd[neighbor])
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

async def main():
    fname, port = parse(sys.argv[1:])
    if not fname:
        raise SystemExit(USAGE)

    global MYNAME 
    MYNAME = fname
    init_logger(MYNAME)
    
    logger.info(f'Starting {MYNAME} on port {port}')
    server = await asyncio.start_server(
        handle_echo, ipaddr, port=port)


    async with server:
        await server.serve_forever()

if __name__=='__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info(f"Keyboard Interrupt. Shutting down.\n")
        sys.exit(0)