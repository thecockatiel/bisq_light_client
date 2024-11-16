import unittest
from utils.data import SimpleProperty, SimplePropertyChangeEvent

class TestSimpleProperty(unittest.TestCase):
    def setUp(self):
        self.int_prop = SimpleProperty[int](42)
        self.str_prop = SimpleProperty[str]("test")

    def test_initialization(self):
        self.assertEqual(self.int_prop.get(), 42)
        self.assertEqual(self.str_prop.get(), "test")

    def test_set_and_get(self):
        self.str_prop.set("updated")
        self.assertEqual(self.str_prop.get(), "updated")
        
        self.int_prop.set(100)
        self.assertEqual(self.int_prop.get(), 100)

    def test_property_decorator(self):
        self.assertEqual(self.str_prop.value, "test")
        self.str_prop.value = "changed"
        self.assertEqual(self.str_prop.value, "changed")

    def test_listener(self):
        events = []
        def listener(event: SimplePropertyChangeEvent[int]):
            events.append(event)

        self.int_prop.add_listener(listener)
        self.int_prop.set(99)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].old_value, 42)
        self.assertEqual(events[0].new_value, 99)

        self.int_prop.remove_listener(listener)
        self.int_prop.set(100)
        self.assertEqual(len(events), 1)  # No new events after removal

    def test_no_event_on_same_value(self):
        events = []
        def listener(event: SimplePropertyChangeEvent[int]):
            events.append(event)

        self.int_prop.add_listener(listener)
        self.int_prop.set(42)  # Same value as initial
        self.assertEqual(len(events), 0)

if __name__ == '__main__':
    unittest.main()
