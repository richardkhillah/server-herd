import unittest

from console import render_dashboard
from herd import ServerStatus


SNAPSHOT = (
    ServerStatus(name="Bailey", port=12345, serving=True, started_at=100.0, clients=frozenset(("a", "b"))),
    ServerStatus(name="Campbell", port=23456, serving=False, started_at=None, clients=frozenset()),
    ServerStatus(name="Clark", port=34567, serving=True, started_at=100.0, clients=frozenset(("b", "c"))),
)
NOW = 165.0


class RenderDashboardTest(unittest.TestCase):
    def setUp(self):
        self.output = render_dashboard(SNAPSHOT, NOW)

    def line_for(self, server_name):
        for line in self.output:
            if line.split()[0] == server_name:
                return line
        self.fail(f"Missing server: {repr(server_name)}")
        
    def test_stopped_servers_show_stopped_with_dash(self):
        line = self.line_for("Campbell").split()
        self.assertEqual(line[2], "stopped")
        self.assertEqual(line[3], "-")

    def test_serving_shows_serving_with_uptime(self):
        bailey, clark = (self.line_for(name).split() for name in ("Bailey", "Clark"))
        self.assertEqual(bailey[2], "serving")
        self.assertEqual(bailey[3], "0:01:05")
        self.assertEqual(clark[2], "serving")
        self.assertEqual(clark[3], "0:01:05")

    def test_6_lines_for_3_servers(self):
        self.assertEqual(len(self.output), 6)

    def test_footer_contains_running_over_total_servers(self):
        footer = self.output[-1].split()
        self.assertEqual(footer[0], "2/3")
        self.assertEqual(footer[1], "serving")

    def test_footer_contains_unique_clients_only(self):
        footer = self.output[-1].split()
        self.assertEqual(footer[-1], "3")


if __name__ == "__main__":
    unittest.main()
