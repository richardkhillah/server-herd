import re
import unittest

from console import render_dashboard, render_frame, HOME, ERASE_TO_EOL, CLEAR_SCREEN, CLEAR_TO_END_OF_SCREEN
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


class RenderFrameTest(unittest.TestCase):
    def test_input_cuts_to_width(self):
        expected_result = HOME + "01234" + ERASE_TO_EOL + CLEAR_TO_END_OF_SCREEN
        result = render_frame(["0123456789"], 5)
        self.assertEqual(result, expected_result)

    def test_input_not_cut(self):
        expected_result = HOME + "01234" + ERASE_TO_EOL + CLEAR_TO_END_OF_SCREEN
        result = render_frame(["01234"], 10)
        self.assertEqual(result, expected_result)

    def test_proper_multiline_formatting_witout_clear(self):
        lines = ["Hello, ", "World!"] ; width = 5
        expected_result = HOME + "Hello" + ERASE_TO_EOL + "\n" + "World" + ERASE_TO_EOL + CLEAR_TO_END_OF_SCREEN
        self.assertEqual(render_frame(lines, width), expected_result)


if __name__ == "__main__":
    unittest.main()
