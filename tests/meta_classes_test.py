import unittest
from utils.meta_classes import Singleton

class TestSingleton(unittest.TestCase):
    def test_basic_singleton(self):
        class TestClass(metaclass=Singleton):
            pass
            
        instance1 = TestClass()
        instance2 = TestClass()
        self.assertIs(instance1, instance2)
    
    def test_singleton_with_args(self):
        class TestClassWithArgs(metaclass=Singleton):
            def __init__(self, value):
                self.value = value
                
        instance1 = TestClassWithArgs(1)
        instance2 = TestClassWithArgs(2)
        self.assertIs(instance1, instance2)
        self.assertEqual(instance1.value, 1)
        
    def test_singleton_attributes(self):
        class TestClassAttrs(metaclass=Singleton):
            def __init__(self):
                self.counter = 0
                
        instance1 = TestClassAttrs()
        instance1.counter = 42
        instance2 = TestClassAttrs()
        self.assertEqual(instance2.counter, 42)
        
    def test_multiple_decorated_classes(self):
        class FirstClass(metaclass=Singleton):
            pass
            
        class SecondClass(metaclass=Singleton):
            pass
            
        first1 = FirstClass()
        first2 = FirstClass()
        second1 = SecondClass()
        second2 = SecondClass()
        
        self.assertIs(first1, first2)
        self.assertIs(second1, second2)
        self.assertIsNot(first1, second1)

    def test_static_variables(self):
        class TestClassStatic(metaclass=Singleton):
            static_var = 42
            class_attr = "test"
            
        # Test direct access
        self.assertEqual(TestClassStatic.static_var, 42)
        self.assertEqual(TestClassStatic.class_attr, "test")
        
        # Test access via instance
        instance = TestClassStatic()
        self.assertEqual(instance.static_var, 42)
        
        # Test modification
        TestClassStatic.static_var = 100
        self.assertEqual(TestClassStatic.static_var, 100)
        self.assertEqual(instance.static_var, 100)

    def test_class_methods(self):
        class TestClassMethods(metaclass=Singleton):
            @classmethod
            def my_class_method(cls):
                return "class_method"
                
            @staticmethod
            def my_static_method():
                return "static_method"
        
        # Test class method access
        self.assertEqual(TestClassMethods.my_class_method(), "class_method")
        instance = TestClassMethods()
        self.assertEqual(instance.my_class_method(), "class_method")
        
        # Test static method access
        self.assertEqual(TestClassMethods.my_static_method(), "static_method")
        self.assertEqual(instance.my_static_method(), "static_method")

    def test_class_attribute_preservation(self):
        class TestClassAttrs(metaclass=Singleton):
            cls_attr = []
            
        TestClassAttrs.cls_attr.append(1)
        instance = TestClassAttrs()
        instance.cls_attr.append(2)
        
        self.assertEqual(TestClassAttrs.cls_attr, [1, 2])
        self.assertIs(TestClassAttrs.cls_attr, instance.cls_attr)

    def test_class_inheritance(self):
        class BaseClass(metaclass=Singleton):
            pass
            
        class SubClass(BaseClass):
            pass
            
        base1 = BaseClass()
        base2 = BaseClass()
        sub1 = SubClass()
        sub2 = SubClass()
        
        self.assertIs(base1, base2)
        self.assertIs(sub1, sub2)
        self.assertIsNot(base1, sub1)
    
if __name__ == '__main__':
    unittest.main()