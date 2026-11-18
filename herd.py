import argparse
import asyncio
import logging
import time
from dataclasses import dataclass

from server import Server, IPADDR
from topology import NEIGHBORS, PORTS

_MINIMUM_REFRESH = 0.1


@dataclass(frozen=True)
class ServerStatus:
    name: str
    port: int
    serving: bool
    started_at: float | None
    clients: frozenset[str]


class Herd:
    def __init__(self, ports: dict[str, int], neighbors: dict[str, list[str]]):
        self._neighbors: dict[str, list[str]] = neighbors
        self._servers: dict[str, Server] = {
            name: Server(name, IPADDR, port, set()) # no neighbors for now
            for name, port in ports.items()
        }
        self._started_at: dict[str, float] = {}

    async def start(self) -> None:
        # Start all servers and record their start times
        for name, server in self._servers.items():
            await server.start()
            self._started_at[name] = time.monotonic()
        # wire the neighbors
        for name, server in self._servers.items():
            server.neighbors = {(n, self._servers[n].port) for n in self._neighbors[name]}

    async def stop(self) -> None:
        for server in self._servers.values():
            await server.stop()

    def snapshot(self) -> tuple[ServerStatus, ...]:
        snap = []
        for name, server in self._servers.items():
            serving=server.is_serving()
            snap.append(ServerStatus(
                name=name,
                port=server.port,
                serving=serving,
                started_at=self._started_at[name] if serving else None,
                clients=frozenset(server.records),
            ))
        return tuple(snap)


def _refresh_type(arg):
    if (a := float(arg)) >= _MINIMUM_REFRESH:
        return a
    raise argparse.ArgumentTypeError(f"must be at least {_MINIMUM_REFRESH}")


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', 
                        default=1.0, 
                        help=f'Seconds between redraws, minimum {_MINIMUM_REFRESH}; (Default: 1.0)',
                        type=_refresh_type
    )
    return parser.parse_args(argv)


async def main():
    logging.basicConfig(level=logging.INFO)
    herd = Herd(PORTS, NEIGHBORS)
    await herd.start()
    try:
        await asyncio.Event().wait() # run until Ctrl-C
    finally:
        await herd.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
