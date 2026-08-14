from datalib.type_processing import *

def test_type_creation():
    new_type = create_annotated_datatype("foo", (int, str))

    assert new_type.__name__ == "foo"
    assert new_type.__annotations__ == {"int": int, "str": str}
