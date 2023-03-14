import ast
import time

from projectExceptions import ParseException, CoordinateException

class Request:
    def __init__(self, message, received_time, payload=None):
        self.type = None
        self.skew = None
        self.addr = None
        self.lon = None
        self.lat = None
        self.radius = None
        self.pagination = None
        self.client_time = None
        self.received_time = received_time
        self._message = message
        self._payload = payload
        self.nodes_visisted = []

        # for shrinking of variables
        self.valid = True # Assume valid unless set otherwise

        try:
            self._message = message
            payload=payload
            if message.strip().startswith(('IAMAT', 'WHATSAT', 'AT')):
                handlers = {
                    'IAMAT': self.parse_iamat,
                    'WHATSAT': self.parse_whatsat,
                    'AT': self.parse_at,
                }
                lengths = {
                    'IAMAT': 4,
                    'WHATSAT': 4,
                }
                m = [s for s in message.strip().split() if len(s)]
                if m[0] in ['IAMAT', 'WHATSAT'] and len(m) != lengths[m[0]]:
                    raise ParseException(f'Invalid {m[0]} length')

                self.type = m[0]
                handlers[self.type](*m[1:])
            else:
                self.mark_invalid()
        except ParseException as pe:
            print(f'INVALID: {pe}')
            self.mark_invalid()

    def parse_iamat(self, addr, coords, timestamp):
        # IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 1621464827.959498503
        self.addr = addr
        try:
            split_coords = self.crude_coord_split(coords)
        except CoordinateException as ce:
            raise ParseException(f'Invalid IAMAT coordiates {ce}')
        if not self.isnumeric(split_coords[1], split_coords[3]):
            raise ParseException('Invalid IAMAT coordinates')
        if not self.isnumeric(timestamp):
            raise ParseException('Invalid IAMAT timestamp')

        self.lat = (split_coords[0], split_coords[1]) # ['+/-', 'floatstring']
        self.lon = (split_coords[2], split_coords[3]) # ['+/-', 'floatstring']
        self.client_time = timestamp
        skew = self.received_time - float(timestamp)
        self.skew = '+'+str(skew) if skew > 0 else str(skew)
    
    def parse_whatsat(self, addr, radius, nresults):
        # WHATSAT kiwi.cs.ucla.edu 10 5
        if not self.isnumeric(radius, nresults):
            raise ParseException(f'Invalid WHATSAT radius and/or num type')
        
        r = int(radius)
        p = int(nresults)
        if r > 50 or r < 0:
            raise ParseException(f"Invalid WHATSAT radius. {r} not between 0 and 50km.")
        if p < 0 or 20 < p:
            raise ParseException(f'Invalid WHATSAT number of responses. {p} not between 0 and 20.')
        
        self.addr = addr
        self.radius = r*1000
        self.pagination = p

    def parse_at(self, peer, skew, addr, coords, timestamp, *args):
        # AT Clark +0.263873386 kiwi.cs.ucla.edu +34.068930-118.445127 1621464827.959498503
        if not len(args) >= 1:
            raise ParseException('Invalid AT length')

        if not self.isnumeric(skew):
            raise ParseException('Invalid AT skew')
        
        self.parse_iamat(addr, coords, timestamp)

        print(f'\nparse_at: {addr=} {coords=} {timestamp=}\n')

        
        self.sender = peer
        self.skew = skew

        try:
            fix = "".join(args)
            self.nodes_visisted = ast.literal_eval(fix)
        except Exception as e:
            raise ParseException(f"Invalid AT visisted {args}")

    def get_visited(self):
        return self.nodes_visisted
    
    def mark_invalid(self):
        self.valid = False
    
    def is_valid(self):
        return self.valid

    def mark_visited(self, name):
        self.nodes_visisted.append(name.strip())

    def was_visited_by(self, name):
        return name in self.nodes_visisted
    
    def __str__(self):
        type = self.type
        skew = self.skew
        addr = self.addr
        lon = self.lon
        lat = self.lat
        radius = self.radius
        pagination = self.pagination
        client_time = self.client_time
        nodes_visited = self.nodes_visisted
        return f"{type=} {skew=} {addr=} {lon=} {lat=} {radius=} {pagination=} {client_time=} {nodes_visited=}"
    
    @property
    def location(self):
        if self.lat is not None and self.lon is not None:
            return "".join([*self.lat, *self.lon])
        else:
            return ""
    
    @property
    def api_location(self):
        if self.lat is not None and self.lon is not None:
            return ",".join([*self.lat, *self.lon])
        else:
            return ""

    def isnumeric(self, *args):
        try:
            for a in args:
                float(a)
            return True
        except:
            return False

    def response(self, at, rec, payload=None):
        if not self.valid:
            return f"? {self._message}"

        s = rec.skew
        a = rec.addr
        b = str(rec.position)
        c = str(rec.client_time)
        r = f"AT {at} {s} {a} {b} {c}\n"
        if payload:
            payload.strip('\n')
        return r if not payload else (r + f"{payload}\n\n")
    
    def flood_response(self, at):
        try:
            a = self.skew
            b = self.addr
            c = str(self.location)
            d = self.client_time
            e = str(self.nodes_visisted)
            r = f"AT {at} {a} {b} {c} {d} {e}"
            return r
        except Exception as e:
            # TODO: How should this be handled?
            print(f'ISSUE IN REQUEST.PY: {e}')
            pass

    def crude_coord_split(self, coordstr):
        # s = '+34.068930-118.445127'
        coords = [c for c in coordstr.replace('-', '+').strip().split('+') if len(c)]
        if len(coords) != 2:
            raise CoordinateException(f'Invalid coordinate lentgh')
        if not self.isnumeric(*coords):
            raise CoordinateException(f'Invalid coordinate {coordstr}')
        
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

    def is_whatsat(self):
        return self.type == 'WHATSAT'
    def is_iamat(self):
        return self.type == 'IAMAT'
    def is_at(self):
        return self.type == 'AT'