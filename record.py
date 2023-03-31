class Record:
    def __init__(self, addr, skew, client_time, position):
        self.addr = addr
        self.skew = skew
        self.client_time = client_time
        self.position = position
        self._new = True

    def __str__(self):
        return f'{self.addr} {self.position}'
    
    def __eq__(self, other):
        return (
            self.addr == other.addr and
            self.skew == other.skew and
            self.client_time == other.client_time and
            self.position == other.position
        )

    def is_new(self):
        return self._new
    
    def mark_notnew(self):
        self._new = False

    def to_message(self, name):
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
    
    def __str__(self):
        return ''.join([self.lat, self.lon])
    
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

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, r):
        try:
            self._radius = int(r) if int(r) <= 1500 else 1500
        except TypeError as te:
            if r is not None:
                raise TypeError('Expected radius of coercable int type.')
            self._radius = None

    @property
    def pagination(self):
        return self._pagination

    @pagination.setter
    def pagination(self, size):
        try:
            self._pagination = int(size) if int(size) <= 20 else 20
        except (TypeError, ValueError) as e:
            if size is not None:
                raise e
            self._pagination = None
        
    def __eq__(self, other):
        return (
            self.lat == other.lat and
            self.lon == other.lon and
            self.radius == other.radius and
            self.pagination == other.pagination and
            self.payload == other.payload
        )
    
    @property
    def api_location(self):
        return ",".join(["".join(self.lat), "".join(self.lon)])