from datalib.queries.speculative.base_attributes import standard
from datalib.queries.speculative import condition_validator, condition_specifier

def setup_env():
    ...

def test_foreign_simple():
    from test.datalib.data import test_data_foreign as td
    condition_specifier.make_module_queryable(td)

    test_attribute: condition_specifier.Attribute = td.ExampleParent["field"]

    assert test_attribute.parent == td.ExampleParent

    attribute_manager = condition_validator.DatatypeConverter(
        type_managers=standard.EXPORTED_TYPE_MANGERS,
        root_attribute_type=standard.EXPORTED_ROOT_TYPE
    )

    test_validated_attribute_collection: condition_validator.AttributeCollection = attribute_manager.validate_attribute(test_attribute)
    test_validated_attribute: condition_validator.AbstractAttribute = test_validated_attribute_collection.attributes[0]

    assert isinstance(test_validated_attribute, standard.FieldTypeAttribute), \
        f"Validated attribute is not of the correct type, expected {standard.FieldTypeAttribute.__name__} but found" \
        f"{type(test_validated_attribute).__name__} instead"

    assert test_validated_attribute.name == "field",\
        f"Incorrect attribute stored, expected 'field' but found {test_validated_attribute.name} instead"

    assert test_validated_attribute.attribute_type == td.ExampleForeign,\
        f"Believed datatype that the attribute is representing is incorrect, expected to think it was of type {td.ExampleForeign.__name__}"\
        f"but was of type {test_validated_attribute.attribute_type.__name__} instead"

    assert (l := len(test_validated_attribute_collection.attributes)) == 1, \
        f"The wrong number of attributes were discovered, expected 1 but instead found {l}"

    assert isinstance(test_validated_attribute.parent, standard.StandardRootTable),\
        f"Expected parent to be a {standard.StandardRootTable.__name__} but instead was"\
        f"{type(test_validated_attribute.parent).__name__}"

    assert test_validated_attribute.parent.name == td.ExampleParent.__name__,\
        f"Parent has incorrect name, expected {td.ExampleParent.__name__} but instead found {test_validated_attribute.parent.name}"

    assert test_validated_attribute.parent.attribute_type == td.ExampleParent,\
        f"Parent is expected to be of type {td.ExampleParent.__name__} but instead was of type {test_validated_attribute.parent.attribute_type.__name__}"


def test_nested_foreign():
    from test.datalib.data import test_data_foreign as td
    condition_specifier.make_module_queryable(td)

    test_attribute = td.ExampleParent["field"]["data"]

    attribute_manager = condition_validator.DatatypeConverter(
        type_managers=standard.EXPORTED_TYPE_MANGERS,
        root_attribute_type=standard.EXPORTED_ROOT_TYPE
    )

    validated_attribute_collection = attribute_manager.validate_attribute(test_attribute)
    validated_attribute: condition_validator.AbstractAttribute = validated_attribute_collection.attributes[0]



def main():
    test_foreign_simple()
    test_nested_foreign()

if __name__ == "__main__":
    main()