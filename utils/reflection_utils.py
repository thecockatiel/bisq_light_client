import ast
from dataclasses import fields
from enum import IntEnum
import inspect

class FieldType(IntEnum):
    DATA = 1
    PROPERTY = 2

def get_settable_fields(cls: type):
    if hasattr(cls, "__dataclass_fields__"):
        # Handle dataclass
        dataclass_fields = [(field.name, FieldType.DATA) for field in fields(cls)]
        property_with_setters = [
            (field, FieldType.PROPERTY)
            for field in cls.__dict__
            if isinstance(getattr(cls, field), property) and getattr(cls, field).fset
        ]
        return dataclass_fields + property_with_setters

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
    self_assignments = []
    if init_method:
        for stmt in init_method.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        if not target.attr.startswith("_"):
                            self_assignments.append((target.attr, FieldType.DATA))
            elif (
                isinstance(stmt, ast.AnnAssign)
                and isinstance(stmt.target, ast.Attribute)
                and stmt.target.value.id == "self"
            ):
                if not stmt.target.attr.startswith("_"):
                    self_assignments.append((stmt.target.attr, FieldType.DATA))

    # Find properties with setters directly from class def
    properties_with_setters = []
    for key in cls.__dict__:
        value = getattr(cls, key)
        if isinstance(value, property) and value.fset:
            properties_with_setters.append((key, FieldType.PROPERTY))

    return self_assignments + properties_with_setters
