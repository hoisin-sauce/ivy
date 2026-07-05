import typing
import types
import utils
import queue
import const

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


def get_dependencies(object_type: typing.Type) -> dict[str, list[typing.Type]]:
    pairings = []
    q = queue.Queue()
    [q.put(i) for i in typing.get_type_hints(object_type).items()]
    while not q.empty():
        s, x = q.get()
        if repr(type(x)) == '<class \'type\'>':
            pairings.append((s,x))
        else:
            [q.put((s, i)) for i in x.__args__]

    fields : dict[str, list[typing.Type]]= dict()
    for key, value in pairings:
        if key not in fields:
            fields[key] = [value]
        else:
            fields[key].append(value)

    return fields

def get_table_contents_from_map(mapping: dict[str, list[typing.Type]]) -> str:
    strings : list[str] = list()
    for key, value in mapping:
        values = len(value)

        assert values != 0

        optional = typing.

        if values == 1:
            if value in const.BASIC_TYPES:
                # add raw field
                ...
            else:
                # add id field
                ...
        else:
            # add the class switch selector thing
            ...


def main():
    import modeldata
    print(get_dependencies(modeldata.ModelResponse))

if __name__ == "__main__":
    main()
