import unittest

from protocol import ClientLocation, IAmAt, ProtocolError, WhatsAt, parse_coordinates, parse_message


CLIENT_LOCATION = {
    "server": "Bailey",
    "skew": 0.0,
    "client": "code.021tech.io",
    "coordinates": "+34.069072065913495-118.44518110210453",
}


class TestProtocol(unittest.TestCase):
    def test_client_location_newer_timestamp_is_newer(self):
        loc1 = ClientLocation(**CLIENT_LOCATION, timestamp='1621464827.959498503')
        loc2 = ClientLocation(**CLIENT_LOCATION, timestamp='1621464840.959498503')
        self.assertTrue(loc2.is_newer_than(loc1))
        self.assertFalse(loc1.is_newer_than(loc2))

    def test_client_location_equal_timestamps_is_not_newer(self):
        loc1 = ClientLocation(**CLIENT_LOCATION, timestamp='1621464827.959498503')
        loc2 = ClientLocation(**CLIENT_LOCATION, timestamp='1621464827.959498503')
        self.assertFalse(loc1.is_newer_than(loc2))
        self.assertFalse(loc2.is_newer_than(loc1))

    def test_client_location_same_timestamp_different_length_is_not_newer(self):
        loc1 = ClientLocation(**CLIENT_LOCATION, timestamp='1621464827.959498503')
        loc2 = ClientLocation(**CLIENT_LOCATION, timestamp='1621464827.9594985030')
        self.assertFalse(loc1.is_newer_than(loc2))
        self.assertFalse(loc2.is_newer_than(loc1))

    def test_valid_coordinates(self):
        cases = [
            ('+34.069072065913495-118.44518110210453', (34.069072065913495, -118.44518110210453)),
            ('+0-110.44518110210453', (0.0, -110.44518110210453)),
            ('+45.0+0', (45.0, 0.0)),
            ('+90-180', (90.0, -180.0)),
            ('-90+180', (-90.0, 180.0)),
        ]
        for case, expected in cases:
            with self.subTest(case=case):
                result = parse_coordinates(case)
                self.assertEqual(result, expected)

    def test_invalid_coordinates_raise_protocol_error(self):
        cases = [
            '+90.5-118.0',
            '-90.5-118.0',
            '+45.0+180.5',
            '+45.0-180.5',
            '45.0-118.44518110210453',
            '+45.0118.44518110210453',
            '+.5-118.44518110210453',
            '+45.-118.44518110210453',
            '+45.0-.5',
            '+45.0-118.',
            '+45.0-118.44518110210453 extra',
            ' +45.0-118.44518110210453',
            ''
        ]
        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(ProtocolError):
                    parse_coordinates(case)

    def test_parse_message_valid_iamat(self):
        message = "IAMAT code.021tech.io +34.069072065913495-118.44518110210453 1621464827.959498503"
        result = parse_message(message)
        self.assertIsInstance(result, IAmAt)
        self.assertEqual(result.client, "code.021tech.io")
        self.assertEqual(result.coordinates, "+34.069072065913495-118.44518110210453")
        self.assertEqual(result.timestamp, "1621464827.959498503")

    def test_parse_message_invalid_iamat(self):
        invalid_messages = [
            "",
            "IAMAT",
            "IAMAT client +34.069072065913495-118.44518110210453",
            "IAMAT client +34.069072065913495-118.44518110210453 extra",
            "IAMAT client +34.069072065913495-118.44518110210453 inf",
            "IAMAT client +34-118 nan", 
            "IAMAT client +34-118 abc", 
            "IAMAT client 34-118 1621464827.9", # (no latitude sign)
            "IAMAT client +91-118 1621464827.9", # (latitude out of range)
            "iamat client +34-118 1621464827.9", # (lowercase command)
        ]
        for message in invalid_messages:
            with self.subTest(message=message):
                with self.assertRaises(ProtocolError):
                    parse_message(message)

    def test_parse_message_valid_whatsat(self):
        valid_messages = [
            ("WHATSAT code.021tech.io 10 5", (10, 5)),
            ("WHATSAT code.021tech.io 50 20", (50, 20)),
        ]
        for message, (radius, limit) in valid_messages:
            with self.subTest(message=message):
                result = parse_message(message)
                self.assertIsInstance(result, WhatsAt)
                self.assertEqual(result.client, "code.021tech.io")
                self.assertEqual(result.radius_km, radius)
                self.assertEqual(result.limit, limit)

    def test_parse_message_invalid_whatsat(self):
        invalid_messages = [
            "",
            "WHATSAT",
            "WHATSAT client 10",
            "WHATSAT client 10 5 extra",
            "WHATSAT client -10 5",
            "WHATSAT client 10 -5",
            "WHATSAT client 51 5",
            "WHATSAT client 10 21",
            "WHATSAT client 0 5",
            "WHATSAT client 10 0",
            "WHATSAT client 10.5 5",
            "WHATSAT client 10 5.5",
        ]
        for message in invalid_messages:
            with self.subTest(message=message):
                with self.assertRaises(ProtocolError):
                    parse_message(message)

    def test_invalid_message(self):
        invalid_messages = [
            "INVALID_MESSAGE code.021tech.io +34.069072065913495-118.44518110210453 1621464827.959498503",
            "python -m unittest test/test_protocol.py",
        ]
        for message in invalid_messages:
            with self.subTest(message=message):
                with self.assertRaises(ProtocolError):
                    parse_message(message)