from types import ModuleType

from datalib.naming import StandardTableNamer
from datalib.schema import TableStructure
from datalib.graph import ClassDependencyGraph
from lm_utils import object_to_dict


def create_schema(module_target: ModuleType) -> TableStructure:
    dependencies = ClassDependencyGraph((module_target,))
    table_structures = TableStructure(dependencies, StandardTableNamer())
    return table_structures

def test_table_access():
    from test.datalib import test_data_foreign as test_module
    schema = create_schema(test_module)
    data_field = schema.table_lookups[test_module.ExampleForeign].get_field("data")
    if data_field:
        print(object_to_dict(data_field))
