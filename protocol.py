from dataclasses import dataclass
import re


class ProtocolError(Exception): ...


ISO6709_RE = re.compile(r"([+-]\d+(?:\.\d+)?)([+-]\d+(?:\.\d+)?)")


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


def parse_coordinates(coordinates: str) -> tuple[float, float]:
    match = ISO6709_RE.fullmatch(coordinates)
    if not match:
        raise ProtocolError(f"Invalid ISO 6709 coordinates: {coordinates}")

    lat, lon = float(match.group(1)), float(match.group(2))
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        raise ProtocolError(f"Coordinates out of bounds: ({lat}, {lon})")

    return lat, lon
