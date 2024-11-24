import unittest

from utils.data import ObservableSet, SimpleProperty, combine_simple_properties

class TestSimpleProperty(unittest.TestCase):
    def setUp(self):
        self.property = SimpleProperty[int](42)
        self.changes = []
    
    def test_initial_value(self):
        self.assertEqual(self.property.get(), 42)
        self.assertEqual(self.property.value, 42)
    
    def test_set_value(self):
        self.property.set(100)
        self.assertEqual(self.property.get(), 100)
        
        # Test property decorator syntax
        self.property.value = 200
        self.assertEqual(self.property.value, 200)
    
    def test_listeners(self):
        def listener(event):
            self.changes.append((event.old_value, event.new_value))
        
        self.property.add_listener(listener)
        self.property.set(1)
        self.property.set(2)
        
        self.assertEqual(self.changes, [(42, 1), (1, 2)])
        
        self.property.remove_listener(listener)
        self.property.set(3)
        
        self.assertEqual(len(self.changes), 2)
    
    def test_no_notification_on_same_value(self):
        self.property.add_listener(lambda e: self.changes.append((e.old_value, e.new_value)))
        self.property.set(42)  # Same as initial value
        
        self.assertEqual(len(self.changes), 0)

    def test_remove_all_listeners(self):
        def listener1(event):
            self.changes.append(1)
        def listener2(event):
            self.changes.append(2)
        
        self.property.add_listener(listener1)
        self.property.add_listener(listener2)
        
        self.property.set(50)
        self.assertEqual(len(self.changes), 2)
        
        self.property.remove_all_listeners()
        self.property.set(60)
        
        # No new changes should be recorded
        self.assertEqual(len(self.changes), 2)
        self.assertEqual(len(self.property._listeners), 0)

class TestCombineSimpleProperties(unittest.TestCase):
    def setUp(self):
        self.prop1 = SimpleProperty[int](1)
        self.prop2 = SimpleProperty[str]("test")
        
    def test_combine_properties(self):
        def transform(values):
            return f"{values[0]}:{values[1]}"
        
        results = []
        
        combined = combine_simple_properties(self.prop1, self.prop2, transform=transform)
        combined.add_listener(lambda e: results.append(e.new_value))
        
        self.assertIsNone(combined.value)
        
        self.prop1.set(62)
        self.prop1.set(42)
        self.assertEqual(results, [])
        
        self.prop2.set("hello")
        
        self.assertEqual(results, ["42:hello"])
        
        self.prop1.set(100)
        self.assertEqual(results, ["42:hello", "100:hello"])
    
    def test_cleanup(self): 
        prop1 = SimpleProperty(1)
        prop2 = SimpleProperty(2)
        
        combined = combine_simple_properties(prop1, prop2, transform=lambda x: sum(x))
        
        
        self.assertEqual(len(prop1._listeners), 0)
        self.assertEqual(len(prop2._listeners), 0)
        self.assertEqual(len(combined._listeners), 0)
        
        def on_sum(x: int):
            pass
        def on_another_sum(x: int):
            pass
        combined.add_listener(on_sum)
        
        self.assertEqual(len(prop1._listeners), 1)
        self.assertEqual(len(prop2._listeners), 1)
        self.assertEqual(len(combined._listeners), 1)
        

        combined.add_listener(on_sum)
        self.assertEqual(len(prop1._listeners), 1)
        self.assertEqual(len(prop2._listeners), 1)
        self.assertEqual(len(combined._listeners), 1)
        

        combined.add_listener(on_another_sum)
        self.assertEqual(len(prop1._listeners), 1)
        self.assertEqual(len(prop2._listeners), 1)
        self.assertEqual(len(combined._listeners), 2)
        
        # Remove listeners
        combined.remove_listener(on_sum)
        self.assertEqual(len(combined._listeners), 1)
        self.assertEqual(len(prop1._listeners), 1)
        self.assertEqual(len(prop2._listeners), 1)
        
        # Remove listeners
        combined.remove_listener(on_another_sum)
        self.assertEqual(len(combined._listeners), 0)
        self.assertEqual(len(prop1._listeners), 0)
        self.assertEqual(len(prop2._listeners), 0)

class TestObservableSet(unittest.TestCase):
    def setUp(self):
        self.set = ObservableSet[int]()
        self.events = []
        
    def test_constructor(self):
        new_set = ObservableSet([1, 2, 3])
        self.assertEqual(len(new_set), 3)

    def test_add(self):
        def listener(set_obj, operation, element):
            self.events.append((operation, element))

        self.set.add_listener(listener)
        
        # Test adding new element
        result = self.set.add(1)
        self.assertTrue(result)
        self.assertEqual(len(self.set), 1)
        self.assertEqual(self.events, [('add', 1)])

        # Test adding existing element
        result = self.set.add(1)
        self.assertFalse(result)
        self.assertEqual(len(self.set), 1)
        self.assertEqual(len(self.events), 1)  # No new event

    def test_remove(self):
        def listener(set_obj, operation, element):
            self.events.append((operation, element))

        self.set.add(1)
        self.set.add_listener(listener)
        
        result = self.set.remove(1)
        self.assertTrue(result)
        self.assertEqual(len(self.set), 0)
        self.assertEqual(self.events, [('remove', 1)])
        
        result = self.set.remove(1)
        self.assertFalse(result)
        self.assertEqual(len(self.set), 0)
        self.assertEqual(len(self.events), 1)   # No new event

    def test_clear(self):
        def listener(set_obj, operation, element):
            self.events.append((operation, element))

        self.set.add(1)
        self.set.add(2)
        self.set.add_listener(listener)
        
        self.set.clear()
        self.assertEqual(len(self.set), 0)
        self.assertEqual(self.events, [('clear', None)])

    def test_listener_management(self):
        events1 = []
        events2 = []

        def listener1(set_obj, operation, element):
            events1.append((operation, element))

        def listener2(set_obj, operation, element):
            events2.append((operation, element))

        self.set.add_listener(listener1)
        self.set.add_listener(listener2)
        
        self.set.add(1)
        self.assertEqual(events1, [('add', 1)])
        self.assertEqual(events2, [('add', 1)])

        self.set.remove_listener(listener1)
        self.set.add(2)
        self.assertEqual(len(events1), 1)  # No new events
        self.assertEqual(events2, [('add', 1), ('add', 2)])

    def test_contains(self):
        self.set.add(1)
        self.assertTrue(1 in self.set)
        self.assertFalse(2 in self.set)

if __name__ == '__main__':
    unittest.main()
