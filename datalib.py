import typing
import types
import utils


class Database:
    def __init__(self, modules: list[types.ModuleType]):
        classes = [get_classes_from_module(i) for i in modules]


def get_classes_from_module(module: types.ModuleType) -> list[typing.Type]:
    classes = []
    for object_name in utils.public_dir(module):
        obj = getattr(module, object_name)
        if type(obj) == typing.Type:
            classes.append(obj)

    return classes


def get_dependencies(object_type: typing.Type) -> list[typing.Type]:
    objects = []
    for _, i in typing.get_type_hints(object_type).items():
        print(i)

def main():
    import modeldata
    get_dependencies(modeldata.ModelResponse)

if __name__ == "__main__":
    main()
