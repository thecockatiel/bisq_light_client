import unittest

from utils.data import SimpleProperty, combine_simple_properties

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
        

if __name__ == '__main__':
    unittest.main()
