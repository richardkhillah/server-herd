import aiohttp
import asyncio
import collections
import json
import logging
import sys
import time

from typing import List, Tuple
from urllib.parse import quote_plus as safe_url

import env
from request import Request
from record import Record, Position

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
        sys.exit(0)
    return name, port

def get_or_create_client_record(msg):
    is_new = False
    try:
        rec = records[msg.addr]
    except:
        rec = Record(
            msg.addr,
            msg.skew,
            msg.client_time,
            Position(msg.lat, msg.lon, 
                     radius=msg.radius, 
                     pagination=msg.pagination, 
                     payload=msg._payload),
        )
        # records[msg.addr] = rec
        is_new = True
    return is_new, rec

TYPE = {
    'IAMAT': None,
    'WHATISAT': None,
    # 'IAM': None,
}

async def handle_echo(reader, writer):
    # Read info from sender
    data = await reader.read() # Want this to be as many as needed
    
    message = data.decode()
    addr = writer.get_extra_info('peername')
    logger.info(f"Received {message} from {addr}")

    # Parse the message. If we have a client 
    request = Request(message, time.time())
    is_new, rec = get_or_create_client_record(request)

    # Do stuff with the record
    if is_new:
        print("NEW")

        # Invalid Request by new Client
        if request.is_whatisat():
            # Need a location before we can answer whatisat
            resp = request.client_response(MYNAME, valid=False)
            logger.debug(f'Error: {resp!r}')
        # New Client
        elif request.is_iamat(): 
            records[rec.addr] = rec
            resp = request.client_response(MYNAME)
            logger.debug(f'New record: {resp!r}')
            #TODO need to update respond to the client and flood
        # Peer Update
        elif request.is_iam():
            # TODO Update my record
            # create peer_response(MYNAME, MYPEERS)
            pass
    else:
        # Update existing Client
        if request.is_iamat():
            # if iamat and location is same, reply to client only
            
            # else update records and flood
            pass
        # Existing Client Query
        elif request.is_whatisat():
            resp = request.client_response('ELIF__IS_WHATISAT')
            # print(f"TEST: {rec.position.radius=} {request.radius=} {rec.position.pagination=} {request.pagination=}")

            if rec.position.radius == request.radius:
                print(f"SHOULDN'T WORK: {rec.position.radius=} {rec.position.pagination=} {request.pagination=}")
                if rec.position.pagination <= request.pagination:
                    print(f'CASE I: {int(rec.position.pagination) <= int(request.pagination)}: {int(rec.position.pagination)=} {int(request.pagination)}')
                #   serve the response with requested pagesize
                elif request.pagination <= 20:
                    print(f'CASE II: {int(rec.position.pagination) <= int(request.pagination)}: {int(rec.position.pagination)=} {int(request.pagination)}')
            #       do api call
            #       update record with new pagesize
            #       serve the client
            #       propagate results throughout
                else:
                    print('INVALID')
            #       invalid resopnse
            else:
                # perform api query
                # api_response = await api_call(rec.position, rec.position.radius)
                api_response = dummy_api_call(rec.position, rec.position.radius)

                # update record
                print("updating record")
                rec.position.radius = request.radius
                rec.position.pagination = request.pagination
                api_response['results'] = \
                    api_response['results'][:int(rec.position.pagination)]
                rec.position.payload = json.dumps(api_response, indent=2)

                # construct client response with payload
                resp = request.client_response(MYNAME, payload=rec.position.payload)

                # construct flood response
                
            pass
        # DOES THIS EVEN HAPPEN?
        elif request.is_iam():
            # TODO: Update my record
            # create peer_response(MYNAME, MYPEERS)
            pass
        else:
            pass


    # Reply to sender
    logger.info(f"Send: {resp}")
    writer.write(resp.encode())
    await writer.drain()

    logger.debug("Close the connection")
    writer.close()
    await writer.wait_closed()

async def main():
    fname, port = parse(sys.argv[1:])
    if not fname:
        raise SystemExit(USAGE)

    MYNAME=fname
    logger.info(f'Starting {MYNAME} on port {port}')
    
    server = await asyncio.start_server(
        handle_echo, ipaddr, port=port)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logger.debug(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

def dummy_api_call(location, radius):
    with open('first_response.json', 'r') as rf:
        data = json.load(rf)

        return data

# async def api_call():
#     async with aiohttp.ClientSession() as session:
#         async with session.get('http://httpbin.org/get') as resp:
#             print(resp.status)
#             print(await resp.text())

async def api_call(location, radius):
    key = env.PLACES_API_KEY
    # url=(
    #     f'https://maps.googleapis.com/maps/api/place/nearbysearch/json' +
    #     f'?location={location}' +
    #     f'&radius={radius}' +
    #     f'&key={key}'
    # )
    url = (
        # f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=-33.8670522%2C151.1957362&radius=50&type=restaurant&keyword=cruise&key={key}"
        f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=-33.8670522%2C151.1957362&radius=50&key={key}"
    )
    ret = None
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return json.loads(await resp.text())

if __name__=='__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info(f"Keyboard Interrupt. Shutting down.\n")
        sys.exit(0)