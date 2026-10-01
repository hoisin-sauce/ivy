from datalib.utils.type_processing import *

def test_type_creation():
    new_type = create_annotated_datatype("foo", (int, str))

    assert new_type.__name__ == "foo"
    assert new_type.__annotations__ == {"int": int, "str": str}

def test_function_argument_shapes():
    from test.datalib.data import test_data_sample_functions as sample_functions
    argument_shape = get_simple_function_argument_shapes(sample_functions.f)

    print(argument_shape)

    method_shape = get_simple_function_argument_shapes(sample_functions.SampleClass.member_method)

    print(method_shape)

    class_method_shape = get_simple_function_argument_shapes(sample_functions.SampleClass.class_method)

    print(class_method_shape)

def main():
    test_function_argument_shapes()

if __name__ == "__main__":
    main()
