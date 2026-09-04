from datalib.queries.speculative import object_attribute_testing
from lm_example_project.lm_utils import object_to_dict, format_with_tabs

def test_basic_creation():
    from test.datalib.data import test_data_query_tables as qt

    object_attribute_testing.make_class_subscriptable(qt.CouldHaveParentOrGrandparent)

    o: object_attribute_testing.ObjectAttribute = qt.CouldHaveParentOrGrandparent["parent_or_grandparent"]

    assert len(o.possible_attributes) == 2

    specialised_o = o[qt.SampleParent]

    assert len(specialised_o.possible_attributes) == 1

    other_specialised_o = qt.CouldHaveParentOrGrandparent["parent_or_grandparent", qt.SampleParent]

    assert len(other_specialised_o.possible_attributes) == 1
    assert format_with_tabs(object_to_dict(specialised_o)) == format_with_tabs(object_to_dict(other_specialised_o))

def test_iterable_creation():
    from test.datalib.data import test_iter_from_markdown as qt

    object_attribute_testing.make_class_subscriptable(qt.ListContainer)

    o: object_attribute_testing.ObjectAttribute = qt.ListContainer["field"]

if __name__ == "__main__":
    test_basic_creation()
    test_iterable_creation()