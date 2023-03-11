import json

class Record:
    def __init__(self, addr, skew, client_time, position):
        self.addr = addr
        self.skew = skew
        self.client_time = client_time
        self.position = position

    def __str__(self):
        return f'{self.addr} {self.position}'
    
    def __eq__(self, other):
        return (
            self.addr == other.addr and
            self.skew == other.skew and
            self.client_time == other.client_time and
            self.position == other.position
        )
    
    def serialize(self):
        return {
            '__record__': True,
            'addr': self.addr, 
            'skew': self.skew, 
            'client_time': self.client_time, 
            'position': self.position.serialize(), 
        }
    
    @classmethod
    def deserialize(cls, dct):
        if '__record__' in dct:
            return cls(
                dct['addr'],
                dct['skew'],
                dct['client_time'],
                Position.deserialize(dct['position']),
            )
    
    def to_message(self, name):
        pass

    def has_changed(self, msg):
        pass

class Position:
    def __init__(self, lat, lon, radius=None, pagination=None, payload=None):
        self.lat = lat
        self.lon = lon
        self.radius=radius
        self.pagination=pagination
        self.payload=payload
    
    def __repr__(self):
        return self.__str__()
    
    @property
    def lat(self):
        return self._lat
    
    @lat.setter
    def lat(self, args):
        try:
            if isinstance(args, str):
                if not args.startswith(('+', '-')):
                    raise ValueError(f'lat error: invalid coordinate string.')
                self._lat = args
            else:
                if len(args) != 2:
                    raise ValueError(f'lat error: expected 2, got {len(args)}.')
                self._lat = ''.join(args)
        except TypeError:
            self._lat = None
    
    @property
    def lon(self):
        return self._lon
    
    @lon.setter
    def lon(self, args):
        try:
            if isinstance(args, str):
                if not args.startswith(('+', '-')):
                    raise ValueError(f'lon error: invalid coordinate string.')
                self._lon = args
            else:
                if len(args) != 2:
                    raise ValueError(f'lon error: expected 2, got {len(args)}.')
                self._lon = ''.join(args)
        except TypeError:
            self._lon = None

    def __str__(self):
        return ''.join([self.lat, self.lon])
    
    def __eq__(self, other):
        return (
            self.lat == other.lat and
            self.lon == other.lon and
            self.radius == other.radius and
            self.pagination == other.pagination and
            self.payload == other.payload
        )
    
    def serialize(self):
        return {
            '__position__': True, 
            'lat': self.lat,
            'lon': self.lon,
            'radius': self.radius,
            'pagination': self.pagination,
            'payload': self.payload,
        }
    
    @classmethod
    def deserialize(cls, dct):
        if '__position__' in dct:
            return cls(
                dct['lat'],
                dct['lon'],
                radius=dct['radius'],
                pagination=dct['pagination'],
                payload=dct['payload'],
            )