from datalib.queries.speculative.base_attributes import standard
from datalib.queries.speculative import condition_validator, condition_specifier

def setup_env():
    ...

def test_foreign_simple():
    from test.datalib.data import test_data_foreign as td
    condition_specifier.make_module_queryable(td)

    test_attribute = td.ExampleParent["field"]

    attribute_manager = condition_validator.DatatypeConverter(
        type_managers=standard.EXPORTED_TYPE_MANGERS,
        root_attribute_type=standard.EXPORTED_ROOT_TYPE
    )

    test_validated_attribute = attribute_manager.validate_attribute(test_attribute)

def main():
    test_foreign_simple()

if __name__ == "__main__":
    main()