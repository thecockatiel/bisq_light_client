import ast
from dataclasses import fields
from enum import IntEnum
import inspect
from typing import Iterable, Union


class FieldType(IntEnum):
    DATA = 1
    PROPERTY = 2

def get_settable_fields(cls: type) -> set[tuple[str, FieldType]]:
    private_fields = []
    public_fields = []
    if hasattr(cls, "__dataclass_fields__"):
        # Handle dataclass
        for field in fields(cls):
            if field.name.startswith("_"):
                private_fields.append((field.name, FieldType.DATA))
            else:
                public_fields.append((field.name, FieldType.DATA))

    # Get source code of the class
    source = inspect.getsource(cls)

    # Parse into AST
    tree = ast.parse(source)
    # Find the class definition in the AST
    class_def = next(node for node in tree.body if isinstance(node, ast.ClassDef))

    # Find the __init__ method
    init_method = next(
        (
            node
            for node in class_def.body
            if isinstance(node, ast.FunctionDef) and node.name == "__init__"
        ),
        None,
    )

    # Find self assignments in __init__
    if init_method:
        for stmt in init_method.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        if target.attr.startswith("_"):
                            private_fields.append((target.attr, FieldType.DATA))
                        else:
                            public_fields.append((target.attr, FieldType.DATA))
            elif (
                isinstance(stmt, ast.AnnAssign)
                and isinstance(stmt.target, ast.Attribute)
                and stmt.target.value.id == "self"
            ):
                if stmt.target.attr.startswith("_"):
                    private_fields.append((stmt.target.attr, FieldType.DATA))
                else:
                    public_fields.append((stmt.target.attr, FieldType.DATA))

    # Find properties with setters directly from class def
    properties_with_setters = []
    for key in cls.__dict__:
        value = getattr(cls, key)
        if (
            isinstance(value, property)
            and value.fset
            and not key.startswith("_")
            and (f"_{key}", FieldType.DATA) in private_fields
        ):
            properties_with_setters.append((key, FieldType.PROPERTY))

    return set(public_fields).union(set(properties_with_setters))

def get_public_fields(cls: type) -> dict[str, FieldType]:
    fields = dict[str, FieldType]()
    if hasattr(cls, "__dataclass_fields__"):
        # Handle dataclass
        for field in fields(cls):
            fields[field.name] = FieldType.DATA

    # Get source code of the class
    source = inspect.getsource(cls)

    # Parse into AST
    tree = ast.parse(source)
    # Find the class definition in the AST
    class_def = next(node for node in tree.body if isinstance(node, ast.ClassDef))

    # Find the __init__ method
    init_method = next(
        (
            node
            for node in class_def.body
            if isinstance(node, ast.FunctionDef) and node.name == "__init__"
        ),
        None,
    )

    # Find self assignments in __init__
    if init_method:
        for stmt in init_method.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        fields[target.attr] = FieldType.DATA
            elif (
                isinstance(stmt, ast.AnnAssign)
                and isinstance(stmt.target, ast.Attribute)
                and stmt.target.value.id == "self"
            ):
                fields[stmt.target.attr] = FieldType.DATA

    # Find properties with setters directly from class def
    properties_with_getters = {}
    for key in cls.__dict__:
        value = getattr(cls, key)
        if (
            isinstance(value, property)
            and value.fget
            and not key.startswith("_")
            and f"_{key}" in fields
        ):
            properties_with_getters[key] = FieldType.PROPERTY
    
    # rebuild fields dict with public props replacing private ones
    rebuilt_fields = {}
    for key, value in fields.items():
        if key.startswith("_"):
            if key[1:] in properties_with_getters:
                rebuilt_fields[key[1:]] = value
            else:
                pass # skip private fields without public getters
        else:
            rebuilt_fields[key] = value

    return rebuilt_fields


def is_instance_of(obj, class_name_or_names: Union[str, Iterable[str]]):
    """
    Check if object implements any of the given class names without imports
    Args:
        obj: Object to check
        class_names: class name(s) to check against
    """

    def get_all_bases(cls):
        bases = set([cls.__name__])
        for base in cls.__bases__:
            bases.update(get_all_bases(base))
        return bases

    obj_bases = get_all_bases(obj.__class__)

    if isinstance(class_name_or_names, str):
        return class_name_or_names in obj_bases
    return any(base in class_name_or_names for base in obj_bases)
