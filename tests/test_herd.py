import asyncio
from contextlib import redirect_stderr
import io
import unittest

from herd import parse_args, Herd
from topology import NEIGHBORS, PORTS
from tests.test_server import send, CLIENT, COORDS, TIMESTAMP


class TopologyTest(unittest.TestCase):
    def test_neighbors_are_symmetric(self):
        for a, neighbors in NEIGHBORS.items():
            for b in neighbors:
                self.assertIn(a, NEIGHBORS[b], f"{a} lists {b}, but {b} doesn't list {a}")


def row_for(snapshot, server_name):
    return {s.name: s for s in snapshot}[server_name]


class HerdTestAsync(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.herd = Herd({name: 0 for name in PORTS}, NEIGHBORS)
        await self.herd.start()

    async def asyncTearDown(self):
        await self.herd.stop()

    async def test_iamat_reaches_jaquez(self):
        await send(row_for(self.herd.snapshot(), "Bailey").port,
                   f"IAMAT {CLIENT} {COORDS} {TIMESTAMP}")

        async def reached():
            while CLIENT not in row_for(self.herd.snapshot(), "Jaquez").clients:
                await asyncio.sleep(0.01)

        await asyncio.wait_for(reached(), timeout=2)

    async def test_snapshot_gives_one_row_per_server(self):
        for snap, name in zip(self.herd.snapshot(), PORTS.keys(), strict=True):
            self.assertEqual(snap.name, name)       # row names match names in PORTS
            self.assertTrue(snap.serving)           # every row running
            self.assertIsNotNone(snap.started_at)   # all started_at
            self.assertNotEqual(snap.port, 0)       # no port 0

    async def test_for_stale_start_time(self):
        await self.herd.stop()
        for snap in self.herd.snapshot():
            self.assertIsNone(snap.started_at)
            self.assertFalse(snap.serving)


class HerdTest(unittest.TestCase):
    def test_empty_list_defaults_to_1(self):
        self.assertEqual(parse_args([]).refresh, 1.0)

    def test_minimum_refresh_boundary_accepted(self):
        self.assertEqual(parse_args(['--refresh', '0.1']).refresh, 0.1)

    def test_below_minimum_refresh_exits(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parse_args(['--refresh', '0.05'])


if __name__=="__main__":
    unittest.main()
    