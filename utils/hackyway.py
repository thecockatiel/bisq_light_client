import types
from typing import Any, Optional, Type, TypeVar, Union

_T = TypeVar("_T")

class _FakeClass:
    
    def __init__(self, original_instance):
        self._fc__original_instance = original_instance

    def __eq__(self, value):
        if hasattr(value, "_fc__original_instance"):
            return id(getattr(value, '_fc__original_instance')) == id(self._fc__original_instance)
        if id(value) == id(self._fc__original_instance):
            return True
        return NotImplemented

def create_fake_copy_of_instance(instance: _T, dict_of_props: Optional[dict[str, Any]] = None) -> _T:
    """
    useful for copying enums with extra properties without affecting the original enum
    
    also patches the original instance to be equal to the fake instance, and calls original eq after that check
    """
    fake_instance = _FakeClass(instance)
    fake_instance.__class__ = instance.__class__
    for prop_name, prop_value in instance.__dict__.items():
        setattr(fake_instance, prop_name, prop_value)
        
    if not hasattr(instance.__class__, '_og_eq_func_'):
        setattr(instance.__class__, '_og_eq_func_', instance.__class__.__eq__)
        def new_eq_func(self, other):
            og_instance = getattr(other, '_fc__original_instance', None)
            if og_instance:
                return id(og_instance) == id(self)
            return instance.__class__._og_eq_func_(self, other)
        instance.__class__.__eq__ = new_eq_func
    
    if dict_of_props:
        for prop_name, prop_value in dict_of_props.items():
            setattr(fake_instance, prop_name, prop_value)
            
    return fake_instance
