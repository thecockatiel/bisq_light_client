import unittest
from utils.data import ObservableList, FilteredList, ObservableChangeEvent

class TestFilteredList(unittest.TestCase):
    def setUp(self):
        # Create source list with a mix of numbers
        self.source = ObservableList([1, 2, 3, 4, 5])
        # Filter even numbers
        self.filtered_list = FilteredList(self.source, lambda x: x % 2 == 0)

    def test_initial_filter(self):
        # Expect only even numbers: 2 and 4
        self.assertEqual(list(self.filtered_list), [2, 4])

    def test_addition_updates_filter(self):
        # Append an even number and an odd number
        self.source.append(6)
        self.source.append(7)
        self.assertIn(6, self.filtered_list)
        self.assertNotIn(7, self.filtered_list)

    def test_removal_updates_filter(self):
        # Remove an even and an odd number
        self.source.remove(2)
        self.assertNotIn(2, self.filtered_list)
        self.source.remove(3)  # odd number; no effect on filter
        self.assertEqual(list(self.filtered_list), [4])

    def test_listener_notification(self):
        events = []
        def listener(event: ObservableChangeEvent[int]):
            events.append((event.added_elements, event.removed_elements))
        self.filtered_list.add_listener(listener)
        # Append an even element -> should trigger an add event
        self.source.append(8)
        # Remove an even element -> should trigger a remove event
        self.source.remove(4)
        expected_events = [
            ([8], None),
            (None, [4])
        ]
        self.assertEqual(events, expected_events)

    def test_changing_filter(self):
        # Change filter to select odd numbers
        self.filtered_list.filter = lambda x: x % 2 != 0
        # Expect initial odd numbers from the source: 1, 3, 5
        self.assertEqual(list(self.filtered_list), [1, 3, 5])
        # Append an odd number and even number, check filtered list updates accordingly
        self.source.append(7)  # odd number, should be added
        self.source.append(8)  # even number, should be ignored
        self.assertEqual(list(self.filtered_list), [1, 3, 5, 7])
        # Remove an odd number and verify removal
        self.source.remove(3)
        self.assertEqual(list(self.filtered_list), [1, 5, 7])
    
    def test_changing_filter_events(self):
        # Setup listener to capture change event when filter is changed
        events = []
        def listener(event: ObservableChangeEvent[int]):
            events.append((event.added_elements, event.removed_elements))
        self.filtered_list.add_listener(listener)
        # Change filter from even to odd:
        # Initial filtered list: [2, 4]
        # New filtered list: [1, 3, 5]
        self.filtered_list.filter = lambda x: x % 2 != 0
        # Verify event: expect added elements [1, 3, 5], removed [2, 4]
        self.assertEqual(len(events), 1)
        added, removed = events[0]
        self.assertEqual(set(added), {1, 3, 5})
        self.assertEqual(set(removed), {2, 4})

if __name__ == '__main__':
    unittest.main()
