import aiohttp
import asyncio
import collections
import json
import logging
import sys
import time

from typing import List, Tuple

import env
from request import Request
from record import Record, Position

logger = logging.getLogger(__name__)

log_to_console = True
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

    # if log_to_console:
    #     c_handler = logging.StreamHandler()

    #     c_handler.setLevel(logging.DEBUG)

    #     c_format = logging.Formatter('%(message)s')

    #     c_handler.setFormatter(c_format)

    #     logger.addHandler(c_handler)


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

# graph = {
#     'Bailey': ['Campbell', 'Bona'],
#     'Bona': ['Clark', 'Jaquez', 'Campbell', 'Bailey'],
#     'Campbell': ['Bailey', 'Bona', 'Jaquez'],
#     'Clark': ['Jaquez', 'Bona'],
#     'Jaquez': ['Clark', 'Bona', 'Campbell'],
# }
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
        # logger.error(f"\"{name}\" not a valid server.")
        sys.exit(0)
    return name, port

def make_position(req):
    return Position(req.lat, req.lon, 
                     radius=req.radius, 
                     pagination=req.pagination, 
                     payload=req._payload)

def update_record(record, req, is_peer=False):
    record.skew = req.skew
    record.client_time = req.client_time
    record.position = make_position(req)
    return record

def make_record(req):
    return Record(
            req.addr,
            req.skew,
            req.client_time,
            make_position(req),
        )

def get_or_create_client_record(req):
    is_new = False
    try:
        rec = records[req.addr]
    except:
        rec = make_record(req)
        is_new = True
    return is_new, rec

TYPE = {
    'IAMAT': None,
    'WHATISAT': None,
    # 'IAM': None,
}

async def do_stuff(reader, writer, request):
    pass

async def handle_echo(reader, writer):
    # Read info from sender
    data = await reader.read() # Want this to be as many as needed
    
    message = data.decode()
    # addr = writer.get_extra_info('peername')
    # logger.info(f"Received {message} at {addr}")
    logger.info(f"Received {message}")

    # Parse the message. If we have a client 
    request = Request(message, time.time())

    # if reqest is valid, process, otherwise trap
    if request.is_valid():
        pass
    else:
        pass

    is_new, rec = get_or_create_client_record(request)
    payload = None
    flood = False
    if not request.is_valid():
        pass
    else:
        # Flood throught network
        if request.is_iam():
            if is_new:
                # print(f'NEW from {request.sender} {str(rec.position)}')
                records[rec.addr] = rec
                flood = True
            # elif str(rec.position) != Position.coords(request.lat, request.lon):
            #     # print(f'UPDATE {str(rec.position)=} to {Position.coords(request.lat, request.lon)=}')
            #     records[rec.addr] =  make_record(request)
            #     flood = True
            # else:
            #     # print(f'END PROP of {str(request)} at {str(rec.position)}')
            #     pass

        # Do stuff with the record
        elif is_new:
            # Invalid Request by new Client
            if request.is_whatisat():
                # Need a location before we can answer whatisat
                request.mark_invalid()

            # New Client
            elif request.is_iamat(): 
                records[rec.addr] = rec
                flood = True
        
        # Update an existing Client
        else:    
            if request.is_iamat():
                # if iamat and location is same, reply to client only
                if str(rec.position) != Position.coords(request.lat, request.lon):
                    # FIXME I don't like how this update is occuring. just make direct like the rest of the code
                    rec = update_record(rec, request)

                    flood = True

            # Existing Client Query
            elif request.is_whatisat():
                if rec.position.radius == request.radius:
                    # serve a subset of previously queried data
                    if request.pagination <= rec.position.pagination:
                        # construct client response with payload
                        payload = json.loads(rec.position.payload)
                        payload['results'] = payload['results'][:request.pagination]
                        payload = json.dumps(payload)

                    # Do an API call to get more results
                    elif rec.position.pagination <= request.pagination:
                        loc = request.api_location
                        rad = request.radius
                        pag = request.pagination
                        logger.debug(f'{request=}')
                        api_response = await api_call(loc, rad, pag)
                        
                        # update record with new pagesize and payload
                        rec.position.pagination = request.pagination
                        rec.position.payload = json.dumps(api_response)
                        payload = rec.position.payload
                    # Invalid response
                    else:
                        request.mark_invalid()
                        raise Exception('Received an invalid exception')

                else:
                    # perform api query
                    # api_response = await api_call(rec.position, rec.position.radius)
                    # with open('places_raw.json', 'w') as f:
                    #     json.dump(api_response, f)

                    # FIXME: location hack. fix this
                    loc = rec.position.api_location
                    rad = request.radius
                    pag = request.pagination
                    logger.debug(f'{str(request)=}')
                    api_response = await api_call(loc, rad, pag)

                    # update record
                    # print("updating record")
                    rec.position.radius = rad
                    rec.position.pagination = pag
                    rec.position.payload = json.dumps(api_response)
                    payload = rec.position.payload
            else:
                # TODO: Do I need to do something here?
                pass
        
    # Respond to Client
    if not request.is_iam():
        resp = request.response(MYNAME, rec, payload=payload)
        
        # Reply to sender
        logger.info(f"Send: {resp}")
        writer.write(resp.encode())
        await writer.drain()

        logger.debug("Close the connection")
        writer.close()
        await writer.wait_closed()

    # Propigate to neighbors
    if request.is_valid() and (request.is_iam() or flood):
        await propagate(request)
        

async def propagate(request: Request):
    request.mark_visited(MYNAME)
    visited = request.get_visited()
    to_visit = [x for x in graph[MYNAME] if x not in visited]
    # to_visit = graph[MYNAME]
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
    # logger.debug(f"api_call({location}, {radius}, {pag}) {url=}")
    # url = (
    #     # f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=-33.8670522%2C151.1957362&radius=50&type=restaurant&keyword=cruise&key={key}"
    #     f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=-33.8670522%2C151.1957362&radius=50&key={key}"
    # )
    ret = None
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.text()
            # print(f'{data=}')
            json_data = json.loads(data)
            # print(f'{json_data=}')/
            if len(results := json_data['results']) >= pag:
                results = results[:pag]

            # return json.loads(await resp.text())
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

    # should I open global connections here?
    
    logger.info(f'Starting {MYNAME} on port {port}')
    server = await asyncio.start_server(
        handle_echo, ipaddr, port=port)

    # addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    # logger.debug(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

if __name__=='__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info(f"Keyboard Interrupt. Shutting down.\n")
        sys.exit(0)