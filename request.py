import json
import time


# class ClientRecord:
#     def __init__(self, msg):
#         self.type = msg.type
#         self.addr = msg.addr
#         self.lon = msg.lon
#         self.lat = msg.lat
    
#     def __str__(self):
#         return f"{self.type} {self.addr} {''.join([*self.lat, *self.lon])}"

class Request:
    def __init__(self, message, received_time=None, payload=None):
        self.type=None
        self.skew=None
        self.addr=None
        self.lon=None
        self.lat=None
        self.radius=None
        self.pagination=None
        self.client_time=None
        self._message=message
        self._payload=payload
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

                if received_time is None:
                    received_time = time.time()
                s = received_time - float(self.client_time)
                self.skew = '+' if s > 0 else '-'
                self.skew += str(s)

            elif type == 'WHATISAT' and len(m) == 4:
                # WHATSAT kiwi.cs.ucla.edu 10 5
                self.type = 'WHATISAT'
                self.addr = m[1]
                try:
                    self.radius = m[2]
                    self.pagination = m[3]
                except:
                    pass
            
    def _body(self):
        b = self.addr
        c = "".join([*self.lat, *self.lon]) if self.type == 'IAMAT' else self.radius
        d = self.client_time if self.type == 'IAMAT' else self.pagination
        return f'{b} {c} {d}'
    
    def __str__(self):
        a = self.type
        b = self._body()
        return f"{a} {b}"
    
    def client_response(self, at, valid=True, payload=None):
        # if self.type not in ('IAMAT', 'WHATISAT'):
        #     return f"? {self._message}"
        if not valid:
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

    def is_whatisat(self):
        return self.type == 'WHATISAT'
    def is_iamat(self):
        return self.type == 'IAMAT'
    def is_iam(self):
        return self.type == 'IAM'