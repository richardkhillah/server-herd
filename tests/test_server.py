import asyncio
import unittest

from server import Server

CLIENT="kiwi.cs.ucla.edu"
COORDS = "+34.068930-118.445127"
TIMESTAMP = "1621464827.959498503"

async def send(port: int, line: str) -> str:
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write((line + '\n').encode())
    await writer.drain()
    writer.write_eof()
    reply = await asyncio.wait_for(reader.read(), timeout=5)
    writer.close()
    await writer.wait_closed()
    return reply.decode()

class SingleServerTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.server = Server("Bailey", "127.0.0.1", 0, set()) #no neighbors
        return await self.server.start()

    async def asyncTearDown(self):
        self.server.server.close()
        await self.server.server.wait_closed()

    def stored_coordinate(self, client: str):
        return str(self.server.records[client].position)

    async def test_iamat_gets_at_reply(self):
        reply = await send(self.server.port, f"IAMAT {CLIENT} {COORDS} {TIMESTAMP}")
        self.assertTrue(reply.startswith("AT Bailey "))
        self.assertIn(f"{CLIENT} {COORDS} {TIMESTAMP}", reply)
        self.assertEqual(self.stored_coordinate(CLIENT), COORDS)

    async def test_whatsat_unknown_client_gets_question_mark(self):
        reply = await send(self.server.port, f"WHATSAT {CLIENT} 10 5")
        self.assertTrue(reply.startswith("? "))

    @unittest.expectedFailure # bug 1: a newer IAMAT is never stored
    async def test_newer_iamat_replaces_location(self):
        await send(self.server.port, f"IAMAT {CLIENT} {COORDS} {TIMESTAMP}") 
        await send(self.server.port, f"IAMAT {CLIENT} +10.000000-20.000000 1621464900.0")
        self.assertEqual(self.stored_coordinate(CLIENT), "+10.000000-20.000000")
    
    @unittest.expectedFailure # bug 2: unknown command crashes the handler
    async def test_unknown_command_gets_question_mark(self):
        reply = await send(self.server.port, "ATTACK ") # ATTACK.startswith("AT")
        self.assertTrue(reply.startswith("? "))
    
    @unittest.expectedFailure # bug 3: bare AT crashes the handler
    async def test_bare_at_gets_question_mark(self):
        reply = await send(self.server.port, "AT")
        self.assertTrue(reply.startswith("? "))
    
    @unittest.expectedFailure # bug 4: unsigned coordinates crash the handler
    async def test_unsigned_coordinates_get_question_mark(self):
        reply = await send(self.server.port, f"IAMAT {CLIENT} 34.068930-118.445127 {TIMESTAMP}")
        self.assertTrue(reply.startswith("? "))

if __name__ == "__main__":
    unittest.main()
