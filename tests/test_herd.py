import asyncio
import unittest

from herd import Herd
from topology import NEIGHBORS, PORTS
from tests.test_server import send, CLIENT, COORDS, TIMESTAMP

class TopologyTest(unittest.TestCase):
    def test_neighbors_are_symmetric(self):
        for a, neighbors in NEIGHBORS.items():
            for b in neighbors:
                self.assertIn(a, NEIGHBORS[b], f"{a} lists {b}, but {b} doesn't list {a}")


class HerdTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.herd = Herd({name: 0 for name in PORTS}, NEIGHBORS)
        await self.herd.start()

    async def asyncTearDown(self):
        await self.herd.stop()

    async def test_iamat_reaches_jaquez(self):
        await send(self.herd._servers["Bailey"].port,
                   f"IAMAT {CLIENT} {COORDS} {TIMESTAMP}")

        async def reached():
            while CLIENT not in self.herd._servers["Jaquez"].records:
                await asyncio.sleep(0.01)

        await asyncio.wait_for(reached(), timeout=2)


if __name__=="__main__":
    unittest.main()