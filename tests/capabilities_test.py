import unittest
from bisq.common.capabilities import Capabilities
from bisq.common.capability import Capability

class TestCapabilities(unittest.TestCase):
    def setUp(self):
        self.empty_capabilities = Capabilities()
        self.test_capabilities = Capabilities([Capability.DAO_STATE, Capability.TRADE_STATISTICS_3])

    def test_initialization(self):
        self.assertTrue(self.empty_capabilities.is_empty())
        self.assertEqual(len(self.test_capabilities.capabilities), 2)

    def test_set_method(self):
        caps = Capabilities()
        new_set = frozenset([Capability.DAO_STATE])
        caps.set(new_set)
        self.assertEqual(caps.capabilities, new_set)

    def test_add_all(self):
        caps = Capabilities([Capability.DAO_STATE])
        caps.add_all([Capability.TRADE_STATISTICS_3])
        self.assertEqual(len(caps.capabilities), 2)
        self.assertTrue(Capability.TRADE_STATISTICS_3 in caps)

    def test_contains_methods(self):
        self.assertTrue(Capability.DAO_STATE in self.test_capabilities)
        self.assertTrue(self.test_capabilities.contains_all({Capability.DAO_STATE}))
        self.assertFalse(Capability.DAO_STATE in self.empty_capabilities)

    def test_is_empty(self):
        self.assertTrue(self.empty_capabilities.is_empty())
        self.assertFalse(self.test_capabilities.is_empty())

    def test_equality(self):
        caps1 = Capabilities([Capability.DAO_STATE])
        caps2 = Capabilities([Capability.DAO_STATE])
        caps3 = Capabilities([Capability.TRADE_STATISTICS_3])
        self.assertEqual(caps1, caps2)
        self.assertNotEqual(caps1, caps3)
        self.assertNotEqual(caps1, "not a capabilities object")

    def test_int_list_conversion(self):
        int_list = Capabilities.to_int_list(self.test_capabilities)
        self.assertIsInstance(int_list, list)
        caps_from_int = Capabilities.from_int_list(int_list)
        self.assertEqual(self.test_capabilities, caps_from_int)

    def test_string_list_conversion(self):
        string_list = "1, 2"
        caps = Capabilities.from_string_list(string_list)
        self.assertFalse(caps.is_empty())
        self.assertEqual(caps.to_string_list(), "1, 2")

    def test_mandatory_capability(self):
        self.assertTrue(Capabilities.has_mandatory_capability(self.test_capabilities))
        self.assertFalse(Capabilities.has_mandatory_capability(self.empty_capabilities))

    def test_pretty_print(self):
        result = self.test_capabilities.pretty_print()
        self.assertIsInstance(result, str)
        self.assertIn("DAO_STATE", result)

    def test_size(self):
        self.assertEqual(len(self.empty_capabilities), 0)
        self.assertEqual(len(self.test_capabilities), 2)

    def test_has_less(self):
        caps1 = Capabilities([Capability.DAO_STATE])
        caps2 = Capabilities([Capability.TRADE_STATISTICS_3])
        self.assertTrue(caps1.has_less(caps2))

    def test_find_highest_capability(self):
        result = self.test_capabilities.find_highest_capability()
        self.assertIsInstance(result, int)
        self.assertTrue(result > 0)

if __name__ == '__main__':
    unittest.main()