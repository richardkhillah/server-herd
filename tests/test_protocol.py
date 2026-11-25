import unittest

from protocol import ClientLocation


ADDR_A = ""
ADDR_B = ""
TIMESTAMP_A = '1621464827.959498503'
TIMESTAMP_B = '1621464840.959498503'
COORDINATES_A = '+34.069072065913495-118.44518110210453'
COORDINATES_B = '+37.827160394635804-122.4229566155028'
CLIENT = 'Bono'


class TestProtocol(unittest.TestCase):
    def test_newer_client_location_passes_is_newer(self):
        loc1 = ClientLocation(server=ADDR_A, skew="0.1", client=CLIENT, coordinates=COORDINATES_A, timestamp=TIMESTAMP_A)
        loc2 = ClientLocation(server=ADDR_A, skew="0.2", client=CLIENT, coordinates=COORDINATES_A, timestamp=TIMESTAMP_B)
        self.assertTrue(loc2.is_newer_than(loc1))
        self.assertFalse(loc1.is_newer_than(loc2))

    def test_equal_client_location_arent_newer(self):
        loc1 = ClientLocation(server=ADDR_A, skew="0.1", client=CLIENT, coordinates=COORDINATES_A, timestamp=TIMESTAMP_A)
        loc2 = ClientLocation(server=ADDR_A, skew="0.1", client=CLIENT, coordinates=COORDINATES_A, timestamp=TIMESTAMP_A)
        self.assertFalse(loc1.is_newer_than(loc2))
        self.assertFalse(loc2.is_newer_than(loc1))

    def test_client_location_of_different_timestamp_length_is_not_newer(self):
        loc1 = ClientLocation(server=ADDR_A, skew="0.1", client=CLIENT, coordinates=COORDINATES_A, timestamp="100.0")
        loc2 = ClientLocation(server=ADDR_A, skew="0.1", client=CLIENT, coordinates=COORDINATES_A, timestamp="100.00")
        self.assertFalse(loc1.is_newer_than(loc2))
        self.assertFalse(loc2.is_newer_than(loc1))