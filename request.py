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
        # if message.strip().startswith(('IAMAT', 'WHATISAT', 'IAM')):
        #     m = message.split()
        #     m = [s.strip() for s in m]
        #     type=m[0]
        #     if type == 'IAMAT' and len(m) == 4:
        #         # IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 1621464827.959498503
        #         self.type = type
        #         self.addr = m[1]
        #         coords = self.crude_coord_split(m[2])
        #         self.lat = (coords[0], coords[1]) # ['+/-', 'floatstring']
        #         self.lon = (coords[2], coords[3]) # ['+/-', 'floatstring']

        #         self.client_time = m[3]

        #         if received_time is None:
        #             received_time = time.time()
        #         s = received_time - float(self.client_time)
        #         self.skew = '+' if s > 0 else '-'
        #         self.skew += str(s)

        #     elif type == 'WHATISAT' and len(m) == 4:
        #         # WHATSAT kiwi.cs.ucla.edu 10 5
        #         self.type = type
        #         self.addr = m[1]
        #         try:
        #             r = int(m[2])
        #             p = int(m[3])
        #             self.radius = r*1000 if r <=50 else 50*1000
        #             self.pagination = p if p <= 20 else 20
        #         except:
        #             pass

        #     elif type == 'IAM':
        #         # print(f'FULL IAM:: {m=}')
        #         self.type = type
        #         self.sender = m[1]
        #         self.skew = m[2]
        #         self.addr = m[3]
        #         coords = self.crude_coord_split(m[4])
        #         self.lat = (coords[0], coords[1]) # ['+/-', 'floatstring']
        #         self.lon = (coords[2], coords[3]) # ['+/-', 'floatstring']
        #         self.client_time = m[5]
        #         try:
        #             fix = "".join(m[6:])
        #             self.nodes_visisted = ast.literal_eval(fix)
        #         except Exception as e:
        #             # TODO: how should this be handled?
        #             before_fix= m[6:]
        #             fix="".join(m[6:])
        #             print(f'ISSUE IN REQUEST.py: {e}: {m[6]=} \n{message=}\n{m=}\n{before_fix=}\n{fix=}')
        #             raise SystemError("F@*!")
        #             self.nodes_visisted = []
        # else:
        #     self.mark_invalid()

        # HOW I WANT TO DO IT
        try:
            self._message = message
            payload=payload
            if message.strip().startswith(('IAMAT', 'WHATISAT', 'AT')):
                handlers = {
                    'IAMAT': self.parse_iamat,
                    'WHATISAT': self.parse_whatisat,
                    'AT': self.parse_at,
                }
                lengths = {
                    'IAMAT': 4,
                    'WHATISAT': 4,
                }
                m = [s for s in message.strip().split() if len(s)]
                if m[0] in ['IAMAT', 'WHATISAT'] and len(m) != lengths[m[0]]:
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
    
    def parse_whatisat(self, addr, radius, nresults):
        # WHATSAT kiwi.cs.ucla.edu 10 5
        if not self.isnumeric(radius, nresults):
            raise ParseException(f'Invalid WHATISAT radius and/or num type')
        
        r = int(radius)
        p = int(nresults)
        if r > 50 or r < 0:
            raise ParseException(f"Invalid WHATISAT radius. {r} not between 0 and 50km.")
        if p < 0 or 20 < p:
            raise ParseException(f'Invalid WHATISAT number of responses. {p} not between 0 and 20.')
        
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
        
        self.sender = peer
        self.skew = skew

        try:
            fix = "".join(*args)
            self.nodes_visisted = ast.literal_eval(fix)
        except Exception as e:
            # TODO: how should this be handled?
            before_fix= args
            fix="".join(*args)
            # print(f'ISSUE IN REQUEST.py: {e}: {m[6]=} \n{message=}\n{m=}\n{before_fix=}\n{fix=}')
            raise SystemError("F@*!")

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

    def response(self, at, rec, herd=False, payload=None):
        if not self.valid:
            return f"? {self._message}"

        s = rec.skew
        a = rec.addr
        b = str(rec.position) if self.type == 'IAMAT' else rec.position.radius
        c = str(rec.client_time) if self.type == 'IAMAT' else rec.position.pagination
        r = f"AT {at} {s} {a} {b} {c}"
        return r if not payload else (r + f"\n{payload}\n")
    
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

    def is_whatisat(self):
        return self.type == 'WHATISAT'
    def is_iamat(self):
        return self.type == 'IAMAT'
    def is_iam(self):
        return self.type == 'IAM'