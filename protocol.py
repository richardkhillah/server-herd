from dataclasses import dataclass


class ProtocolError(Exception): ...


@dataclass(frozen=True)
class IAmAt:
    client: str
    coordinates: str
    timestamp: str


@dataclass(frozen=True)
class WhatsAt:
    client: str
    radius_km: int
    limit: int


@dataclass(frozen=True)
class ClientLocation:
    server: str
    skew: float
    client: str
    coordinates: str
    timestamp: str

    def is_newer_than(self, other: "ClientLocation") -> bool:
        return float(self.timestamp) > float(other.timestamp)