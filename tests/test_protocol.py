import unittest

from protocol import ClientLocation, ProtocolError, parse_coordinates


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
