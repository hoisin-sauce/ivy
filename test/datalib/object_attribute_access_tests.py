from datalib import object_attribute_testing
from lm_utils import object_to_dict, format_with_tabs

def test_basic_creation():
    from test.datalib import test_data_query_tables as qt

    object_attribute_testing.make_class_subscriptable(qt.CouldHaveParentOrGrandparent)

    o = qt.CouldHaveParentOrGrandparent["parent_or_grandparent"]

    print()
    print(format_with_tabs(object_to_dict(o)))

if __name__ == "__main__":
    test_basic_creation()