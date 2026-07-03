import typing
import types
import utils
import queue


class Database:
    def __init__(self, modules: list[types.ModuleType]):
        classes = [get_classes_from_module(i) for i in modules]


def get_classes_from_module(module: types.ModuleType) -> list[typing.Type]:
    classes = []
    for object_name in utils.public_dir(module):
        obj = getattr(module, object_name)
        if repr(type(obj)) == '<class \'type\'>':
            classes.append(obj)

    return classes


def get_dependencies(object_type: typing.Type) -> list[typing.Type]:
    objects = []
    q = queue.Queue()
    [q.put(i) for i in typing.get_type_hints(object_type).items()]
    while not q.empty():
        s, x = q.get()
        if repr(type(x)) == '<class \'type\'>':
            objects.append(x)
        else:
            print(type(x))
            [q.put((s, i)) for i in x.__args__]

    print(objects)

def main():
    import modeldata
    print(get_classes_from_module(modeldata))
    get_dependencies(modeldata.ModelResponse)

if __name__ == "__main__":
    main()
