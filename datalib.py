import enum
import time
import typing
import types
import utils
import queue
import const
from utils import flatten_to_list


class Database:
    def __init__(self, modules: list[types.ModuleType]):
        classes: list[typing.Type] = \
            utils.flatten_to_list([get_classes_from_module(i) for i in modules])

        dependency_map: dict[typing.Type, set[typing.Type]] = {}
        resolved_dependencies: set[typing.Type] = const.BASIC_TYPES
        resolution_order: list[typing.Type] = list()

        print(classes)

        while len(classes) != 0:
            print(len(classes))
            current_type = classes.pop(0)
            print(current_type)
            time.sleep(0.1)

            if current_type not in dependency_map:

                current_field_dependencies = get_dependencies(current_type)
                dependency_map[current_type] = set(utils.flatten_to_list(current_field_dependencies.values()))

            if issubclass(current_type, const.INHERIT_EXCEPTIONS):
                if issubclass(current_type, enum.Enum):
                    ...
                else:
                    resolved_dependencies.add(current_type)

            if not dependency_map[current_type].issubset(resolved_dependencies):
                print(dependency_map[current_type], resolved_dependencies)
                print(f"Appending {current_type}, {dependency_map[current_type]-resolved_dependencies}")
                [classes.append(i) for i in dependency_map[current_type]-resolved_dependencies if i not in classes]
                classes.append(current_type)
                continue

            # we can now actually place it in order
            resolution_order.append(current_type)
            resolved_dependencies.add(current_type)

        print(resolution_order)


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
        if isinstance(x, type):
            pairings.append((s,x))
        elif x in const.TYPE_EXCEPTIONS or utils.safe_is_subclass(x, const.INHERIT_EXCEPTIONS):
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

def get_table_contents_from_map(mapping: dict[str, list[typing.Type]]) -> \
        tuple[str, list[typing.Type]]:
    strings : list[str] = list()
    for key, value in mapping:
        values = len(value)

        assert values != 0

        optional = ...

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

    return "", []

def main():
    import modeldata
    Database([modeldata])

if __name__ == "__main__":
    main()
