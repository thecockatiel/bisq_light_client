import unittest

from utils.data import ObservableChangeEvent, ObservableList, ObservableSet, ObservableMap, SimpleProperty, combine_simple_properties

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

    def test_equality(self):
        prop1 = SimpleProperty[int](42)
        prop2 = SimpleProperty[int](42)
        prop3 = SimpleProperty[int](100)
        
        # Test equality between SimpleProperties
        self.assertEqual(prop1, prop2)
        self.assertNotEqual(prop1, prop3)
        
        # Test equality with raw values
        self.assertEqual(prop1, 42)
        self.assertNotEqual(prop1, 100)
        
        # Test hash equality
        self.assertEqual(hash(prop1), hash(prop2))
        self.assertNotEqual(hash(prop1), hash(prop3))

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
        def listener(set_obj, event):
            self.events.append((event.added_elements, event.removed_elements))

        self.set.add_listener(listener)
        
        # Test adding new element
        result = self.set.add(1)
        self.assertTrue(result)
        self.assertEqual(len(self.set), 1)
        self.assertEqual(self.events, [([1], None)])

        # Test adding existing element
        result = self.set.add(1)
        self.assertFalse(result)
        self.assertEqual(len(self.set), 1)
        self.assertEqual(len(self.events), 1)  # No new event

    def test_remove(self):
        def listener(set_obj, event):
            self.events.append((event.added_elements, event.removed_elements))

        self.set.add(1)
        self.set.add_listener(listener)
        
        result = self.set.remove(1)
        self.assertTrue(result)
        self.assertEqual(len(self.set), 0)
        self.assertEqual(self.events, [(None, [1])])
        
        result = self.set.remove(1)
        self.assertFalse(result)
        self.assertEqual(len(self.set), 0)
        self.assertEqual(len(self.events), 1)  # No new event

    def test_clear(self):
        def listener(set_obj, event):
            self.events.append((event.added_elements,
                              event.removed_elements))

        self.set.add(1)
        self.set.add(2)
        self.set.add_listener(listener)
        
        self.set.clear()
        self.assertEqual(len(self.set), 0)
        self.assertEqual(self.events, [(None, [1, 2])])

    def test_listener_management(self):
        events1 = []
        events2 = []

        def listener1(set_obj, event):
            events1.append((event.added_elements,
                          event.removed_elements))

        def listener2(set_obj, event):
            events2.append((event.added_elements,
                          event.removed_elements))

        self.set.add_listener(listener1)
        self.set.add_listener(listener2)
        
        self.set.add(1)
        expected = [([1], None)]
        self.assertEqual(events1, expected)
        self.assertEqual(events2, expected)

        self.set.remove_listener(listener1)
        self.set.add(2)
        self.assertEqual(len(events1), 1)  # No new events
        self.assertEqual(events2, [([1], None), ([2], None)])

class TestObservableMap(unittest.TestCase):
    def setUp(self):
        self.map = ObservableMap[str, int]()
        self.events = []
        
    def test_constructor(self):
        new_map = ObservableMap({'a': 1, 'b': 2})
        self.assertEqual(len(new_map), 2)
        self.assertEqual(new_map['a'], 1)
        self.assertEqual(new_map['b'], 2)

    def test_set_item(self):
        def listener(event):
            self.events.append((event.added_elements,
                              event.removed_elements))

        self.map.add_listener(listener)
        
        self.map['a'] = 1
        self.assertEqual(len(self.map), 1)
        self.assertEqual(self.events, [([('a', 1)], None)])

        self.map['a'] = 2
        self.assertEqual(len(self.map), 1)
        self.assertEqual(self.events, [
            ([('a', 1)], None),
            ([('a', 2)], None)
        ])

    def test_del_item(self):
        def listener(event):
            self.events.append((event.added_elements,
                              event.removed_elements))

        self.map['a'] = 1
        self.map.add_listener(listener)
        
        del self.map['a']
        self.assertEqual(len(self.map), 0)
        self.assertEqual(self.events, [(None, [('a', 1)])])
        
        # Test deleting non-existent key
        del self.map['a']  # Should not raise or trigger event
        self.assertEqual(len(self.events), 1)  # No new event

    def test_clear(self):
        def listener(event):
            self.events.append((event.added_elements,
                              event.removed_elements))

        self.map['a'] = 1
        self.map['b'] = 2
        self.map.add_listener(listener)
        
        self.map.clear()
        self.assertEqual(len(self.map), 0)
        self.assertEqual(self.events, [(None, [('a', 1), ('b', 2)])])

    def test_update(self):
        def listener(event):
            self.events.append((event.added_elements,
                              event.removed_elements))

        self.map.add_listener(listener)
        
        self.map.update({'a': 1, 'b': 2})
        self.assertEqual(len(self.map), 2)
        self.assertEqual(self.events, [([('a', 1), ('b', 2)], None)])

    def test_listener_management(self):
        events1 = []
        events2 = []

        def listener1(event):
            events1.append((event.added_elements,
                          event.removed_elements))

        def listener2(event):
            events2.append((event.added_elements,
                          event.removed_elements))

        self.map.add_listener(listener1)
        self.map.add_listener(listener2)
        
        self.map['a'] = 1
        expected = [([('a', 1)], None)]
        self.assertEqual(events1, expected)
        self.assertEqual(events2, expected)

        self.map.remove_listener(listener1)
        self.map['b'] = 2
        self.assertEqual(len(events1), 1)  # No new events
        self.assertEqual(events2, [([('a', 1)], None), ([('b', 2)], None)])

class TestObservableList(unittest.TestCase):
    def setUp(self):
        self.list = ObservableList[int]()
        self.events = []
        
    def test_constructor(self):
        new_list = ObservableList([1, 2, 3])
        self.assertEqual(len(new_list), 3)
        self.assertEqual(list(new_list), [1, 2, 3])

    def test_append(self):
        def listener(list_obj, event):
            self.events.append((event.added_elements,
                              event.removed_elements))

        self.list.add_listener(listener)
        
        self.list.append(1)
        self.assertEqual(len(self.list), 1)
        self.assertEqual(self.events, [([1], None)])

    def test_extend(self):
        def listener(list_obj, event):
            self.events.append((event.added_elements,
                              event.removed_elements))

        self.list.add_listener(listener)
        
        self.list.extend([1, 2, 3])
        self.assertEqual(len(self.list), 3)
        self.assertEqual(self.events, [([1, 2, 3], None)])

    def test_insert(self):
        def listener(list_obj, event):
            self.events.append((event.added_elements,
                              event.removed_elements))

        self.list.extend([1, 2, 3])
        self.list.add_listener(listener)
        
        self.list.insert(1, 4)
        self.assertEqual(list(self.list), [1, 4, 2, 3])
        self.assertEqual(self.events, [([4], None)])

    def test_remove(self):
        def listener(list_obj, event):
            self.events.append((event.added_elements,
                              event.removed_elements))

        self.list.extend([1, 2, 3])
        self.list.add_listener(listener)
        
        self.list.remove(2)
        self.assertEqual(list(self.list), [1, 3])
        self.assertEqual(self.events, [(None, [2])])

    def test_pop(self):
        def listener(list_obj, event):
            self.events.append((event.added_elements,
                              event.removed_elements))

        self.list.extend([1, 2, 3])
        self.list.add_listener(listener)
        
        value = self.list.pop()
        self.assertEqual(value, 3)
        self.assertEqual(list(self.list), [1, 2])
        self.assertEqual(self.events, [(None, [3])])
        
        value = self.list.pop(0)
        self.assertEqual(value, 1)
        self.assertEqual(list(self.list), [2])
        self.assertEqual(self.events, [(None, [3]), (None, [1])])

    def test_clear(self):
        def listener(list_obj, event):
            self.events.append((event.added_elements,
                              event.removed_elements))

        self.list.extend([1, 2, 3])
        self.list.add_listener(listener)
        
        self.list.clear()
        self.assertEqual(len(self.list), 0)
        self.assertEqual(self.events, [(None, [1, 2, 3])])

    def test_setitem(self):
        def listener(list_obj, event):
            self.events.append((event.added_elements,
                              event.removed_elements))

        self.list.extend([1, 2, 3])
        self.list.add_listener(listener)
        
        self.list[1] = 4
        self.assertEqual(list(self.list), [1, 4, 3])
        self.assertEqual(self.events, [
            ([4], [2])
        ])

    def test_delitem(self):
        def listener(list_obj, event):
            self.events.append((event.added_elements,
                              event.removed_elements))

        self.list.extend([1, 2, 3])
        self.list.add_listener(listener)
        
        del self.list[1]
        self.assertEqual(list(self.list), [1, 3])
        self.assertEqual(self.events, [(None, [2])])

    def test_listener_management(self):
        events1 = []
        events2 = []

        def listener1(list_obj, event):
            events1.append(event)

        def listener2(list_obj, event):
            events2.append(event)

        self.list.add_listener(listener1)
        self.list.add_listener(listener2)
        
        self.list.append(1)
        self.assertEqual(events1, [ObservableChangeEvent([1])])
        self.assertEqual(events2, [ObservableChangeEvent([1])])

        self.list.remove_listener(listener1)
        self.list.append(2)
        self.assertEqual(len(events1), 1)  # No new events
        self.assertEqual(events2, [ObservableChangeEvent([1]), ObservableChangeEvent([2])])

        self.list.remove_all_listeners()
        self.list.append(3)
        self.assertEqual(len(events1), 1)  # No new events
        self.assertEqual(len(events2), 2)  # No new events

if __name__ == '__main__':
    unittest.main()
