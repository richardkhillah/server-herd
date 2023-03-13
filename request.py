import ast
import json
import time

class Request:
    def __init__(self, message, received_time=None, payload=None):
        self.type = None
        self.skew = None
        self.addr = None
        self.lon = None
        self.lat = None
        self.radius = None
        self.pagination = None
        self.client_time = None
        self._message = message
        self._payload = payload
        self.nodes_visisted = []

        # for shrinking of variables
        self.valid = True # Assume valid unless set otherwise

        if message.startswith(('IAMAT', 'WHATISAT', 'IAM')):
            m = message.split()
            type=m[0]
            if type == 'IAMAT' and len(m) == 4:
                # IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 1621464827.959498503
                self.type = type
                self.addr = m[1]
                coords = self.crude_coord_split(m[2])
                self.lat = (coords[0], coords[1]) # ['+/-', 'floatstring']
                self.lon = (coords[2], coords[3]) # ['+/-', 'floatstring']
                self.client_time = m[3]

                if received_time is None:
                    received_time = time.time()
                s = received_time - float(self.client_time)
                self.skew = '+' if s > 0 else '-'
                self.skew += str(s)

            elif type == 'WHATISAT' and len(m) == 4:
                # WHATSAT kiwi.cs.ucla.edu 10 5
                self.type = type
                self.addr = m[1]
                try:
                    r = int(m[2])
                    p = int(m[3])
                    self.radius = r if r <=50 else 50
                    self.pagination = p if p <= 20 else 20
                except:
                    pass

            elif type == 'IAM':
                self.type = type
                self.sender = m[1]
                self.skew = m[2]
                self.addr = m[3]
                coords = self.crude_coord_split(m[4])
                self.lat = (coords[0], coords[1]) # ['+/-', 'floatstring']
                self.lon = (coords[2], coords[3]) # ['+/-', 'floatstring']
                self.client_time = m[5]
                try:
                    print(f'{m[6]=}')
                    self.nodes_visisted = ast.literal_eval(m[6])
                except Exception as e:
                    # TODO: how should this be handled?
                    print(f'ISSUE IN REQUEST.py: {e}')
                    self.nodes_visisted = []

    def get_visited(self):
        return self.nodes_visisted
    
    def mark_invalid(self):
        self.valid = False

    def mark_visited(self, name):
        self.nodes_visisted.append(name)

    def was_visited_by(self, name):
        return name in self.nodes_visisted
    
    def __str__(self):
        a = self.type
        b = self._body()
        return f"{a} {b}"
    
    @property
    def location(self):
        if self.lat is not None and self.lon is not None:
            return "".join([*self.lat, *self.lon])
        else:
            return ""

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
            c = self.location
            d = self.client_time
            e = str(self.nodes_visisted)
            r = f"IAM {at} {a} {b} {c} {d} {e}"
            return r
        except Exception as e:
            # TODO: How should this be handled?
            print(f'ISSUE IN REQUEST.PY: {e}')
            pass

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

    def is_whatisat(self):
        return self.type == 'WHATISAT'
    def is_iamat(self):
        return self.type == 'IAMAT'
    def is_iam(self):
        return self.type == 'IAM'