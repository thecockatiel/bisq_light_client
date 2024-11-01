import unittest
from utils.class_decorators import Singleton

class TestSingleton(unittest.TestCase):
    def test_basic_singleton(self):
        @Singleton
        class TestClass:
            pass
            
        instance1 = TestClass()
        instance2 = TestClass()
        self.assertIs(instance1, instance2)
    
    def test_singleton_with_args(self):
        @Singleton
        class TestClassWithArgs:
            def __init__(self, value):
                self.value = value
                
        instance1 = TestClassWithArgs(1)
        instance2 = TestClassWithArgs(2)
        self.assertIs(instance1, instance2)
        self.assertEqual(instance1.value, 1)
        
    def test_singleton_attributes(self):
        @Singleton
        class TestClassAttrs:
            def __init__(self):
                self.counter = 0
                
        instance1 = TestClassAttrs()
        instance1.counter = 42
        instance2 = TestClassAttrs()
        self.assertEqual(instance2.counter, 42)
        
    def test_multiple_decorated_classes(self):
        @Singleton
        class FirstClass:
            pass
            
        @Singleton
        class SecondClass:
            pass
            
        first1 = FirstClass()
        first2 = FirstClass()
        second1 = SecondClass()
        second2 = SecondClass()
        
        self.assertIs(first1, first2)
        self.assertIs(second1, second2)
        self.assertIsNot(first1, second1)

if __name__ == '__main__':
    unittest.main()