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
f_handler = logging.FileHandler('new_log.log', mode="w")
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

def get_or_create_client_record(req):
    is_new = False
    try:
        rec = records[req.addr]
    except:
        rec = Record(
            req.addr,
            req.skew,
            req.client_time,
            make_position(req),
        )
        # records[req.addr] = rec
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
        # Invalid Request by new Client
        if request.is_whatisat():
            # Need a location before we can answer whatisat
            resp = request.client_response(MYNAME, valid=False)

        # New Client
        elif request.is_iamat(): 
            records[rec.addr] = rec
            resp = request.client_response(MYNAME)
            
            #TODO need to flood

        # Peer Update
        elif request.is_iam():
            # TODO Update my record
            # create peer_response(MYNAME, MYPEERS)
            pass
    else:
        # Update existing Client
        if request.is_iamat():
            # if iamat and location is same, reply to client only
            if str(rec.position) != Position.coords(request.lat, request.lon):
                # FIXME I don't like how this update is occuring. just make direct like the rest of the code
                rec = update_record(rec, request)
                resp = request.client_response(MYNAME)

                # TODO: Flood response
            else:
                resp = request.client_response('NO__UPDATE__NEEDED__IAMAT')
            # else update records and flood

        # Existing Client Query
        elif request.is_whatisat():
            if rec.position.radius == request.radius:
                # serve a subset of previously queried data
                if request.pagination <= rec.position.pagination:
                    print(f'CASE I: {request.pagination <= rec.position.pagination}: {rec.position.pagination=} {request.pagination=}')

                    # construct client response with payload
                    payload = json.loads(rec.position.payload)
                    payload['results'] = payload['results'][:request.pagination]
                    payload = json.dumps(payload)
                    
                    # serve the response with requested pagesize
                    resp = request.client_response(MYNAME, payload=payload)

                # Do an API call to get more results
                elif rec.position.pagination <= request.pagination:
                    print(f'CASE II: {rec.position.pagination <= request.pagination}: {rec.position.pagination=} {request.pagination=}')
                    
                    # do api call
                    loc = request.location
                    rad = request.radius
                    pag = request.pagination
                    api_response = dummy_api_call(loc, rad, pag)
                    
                    # update record with new pagesize and payload
                    rec.position.pagination = request.pagination
                    rec.position.payload = json.dumps(api_response)

                    # serve the client
                    resp = request.client_response(MYNAME, payload=rec.position.payload)

                    # propagate results throughout
                else:
                    resp = request.client_response('EXISTING INVLAID', payload=rec.position.payload)
            # invalid resopnse
            else:
                # perform api query
                # api_response = await api_call(rec.position, rec.position.radius)
                # with open('places_raw.json', 'w') as f:
                #     json.dump(api_response, f)

                loc = request.location
                rad = request.radius
                pag = request.pagination
                api_response = dummy_api_call(loc, rad, pag)

                # update record
                print("updating record")
                rec.position.radius = rad
                rec.position.pagination = pag
                rec.position.payload = json.dumps(api_response)

                # construct client response with payload
                resp = request.client_response(MYNAME, payload=rec.position.payload)

                # construct flood response
                
        # DOES THIS EVEN HAPPEN?
        elif request.is_iam():
            # TODO: Update my record
            # create peer_response(MYNAME, MYPEERS)
            resp = request.client_response('DOES THIS EVEN HAPPEN?')
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

def dummy_api_call(location, radius, pagination):
    with open('places_raw.json', 'r') as rf:
        data = json.load(rf)
        print(f'{pagination=}')
        data['results'] = data['results'][:pagination]
        return data

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

async def main():
    fname, port = parse(sys.argv[1:])
    if not fname:
        raise SystemExit(USAGE)

    global MYNAME 
    MYNAME = fname
    logger.info(f'Starting {MYNAME} on port {port}')
    
    server = await asyncio.start_server(
        handle_echo, ipaddr, port=port)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logger.debug(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

if __name__=='__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info(f"Keyboard Interrupt. Shutting down.\n")
        sys.exit(0)