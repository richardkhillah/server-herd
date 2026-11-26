from dataclasses import dataclass
import math
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


def _raise_for_invalid_timestamp(ts: str) -> None:
    try:
        ts = float(ts)
        if not math.isfinite(ts):
            raise ProtocolError(f"Invalid timestamp: {ts}")
    except ValueError:
        raise ProtocolError(f"Invalid timestamp: {ts}")


def parse_message(message: str) -> IAmAt | WhatsAt | ClientLocation:
    parts = message.split()
    if not parts:
        raise ProtocolError("Empty message")

    # match commands
    match parts[0]:
        case "IAMAT" if len(parts) == 4:
            parse_coordinates(parts[2])  # validate coordinates
            _raise_for_invalid_timestamp(parts[3])
            return IAmAt(client=parts[1], coordinates=parts[2], timestamp=parts[3])
        case "WHATSAT" if len(parts) == 4:
            try:
                radius = int(parts[2])
                limit = int(parts[3])
                if not ((0 < radius <= 50) and (0 < limit <= 20)):
                    raise ProtocolError(f"Invalid WHATSAT message: {message}")
            except ValueError:
                raise ProtocolError(f"Invalid WHATSAT message: {message}")
            return WhatsAt(client=parts[1], radius_km=radius, limit=limit)
        case "AT" if len(parts) == 6:
            # Valid Format: `AT Clark +0.263873386 kiwi.cs.ucla.edu +34.068930-118.445127 1621464827.959498503`
            try:
                skew = float(parts[2])
                if not math.isfinite(skew):
                    raise ProtocolError(f"Invalid AT message: {message}")
                parse_coordinates(parts[4])  # validate coordinates
                _raise_for_invalid_timestamp(parts[5])
            except ValueError:
                raise ProtocolError(f"Invalid AT message: {message}")
            return ClientLocation(
                server=parts[1],
                skew=skew,
                client=parts[3],
                coordinates=parts[4],
                timestamp=parts[5],
            )
        case _:
            err = "Invalid" if parts[0] in {"IAMAT", "WHATSAT", "AT"} else "Unknown"
            raise ProtocolError(f"{err} command: {parts[0]}")


def format_location(location: ClientLocation) -> str:
    return f"AT {location.server} {location.skew:+} {location.client} {location.coordinates} {location.timestamp}"


def format_invalid(line: str) -> str:
    return f"? {line.rstrip('\n')}"
