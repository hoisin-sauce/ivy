from datalib.queries.speculative import condition_specifier

class TestEntryPoint(condition_specifier.QueryableTable):
    ...

def test_base_getitem_attribute():
    example_attribute = TestEntryPoint["field"]

    assert isinstance(example_attribute, condition_specifier.Attribute)
    assert example_attribute.parent == TestEntryPoint
    assert example_attribute.accessed_by == condition_specifier.AccessMethod.GETITEM
    assert example_attribute.accessed_with == "field"

def test_nested_getitem_attribute():
    example_attribute = TestEntryPoint["field"]
    example_nested_getitem_attribute = example_attribute["other_field"]

    assert isinstance(example_attribute, condition_specifier.Attribute)
    assert example_nested_getitem_attribute.parent == example_attribute
    assert example_nested_getitem_attribute.accessed_by == condition_specifier.AccessMethod.GETITEM
    assert example_nested_getitem_attribute.accessed_with == "other_field"

def test_nested_getattr_attribute():
    example_attribute = TestEntryPoint["field"]
    example_nested_getitem_attribute = example_attribute.other_field

    assert isinstance(example_attribute, condition_specifier.Attribute)
    assert example_nested_getitem_attribute.parent == example_attribute
    assert example_nested_getitem_attribute.accessed_by == condition_specifier.AccessMethod.GETATTR
    assert example_nested_getitem_attribute.accessed_with == "other_field"

def test_condition_creation_eq():
    example_attribute: condition_specifier.Attribute = TestEntryPoint["field"]
    example_condition: condition_specifier.Condition = example_attribute == 1

    assert isinstance(example_condition, condition_specifier.Condition)
    assert example_condition.left == example_attribute
    assert example_condition.right == 1
    assert example_condition.operator == condition_specifier.AttributeComparison.EQ

def test_example_callable_attribute():
    example_callable = TestEntryPoint["field"].option(0)