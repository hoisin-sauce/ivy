import enum
import time
import typing
import types
import utils
import queue
import const
from utils import flatten_to_list
from collections.abc import Iterable


class Database:
    def __init__(self, modules: list[types.ModuleType]):
        classes: list[typing.Type] = \
            utils.flatten_to_list([get_classes_from_module(i) for i in modules])

        dependency_map: dict[typing.Type, set[typing.Type]] = {}
        resolved_dependencies: set[typing.Type] = const.BASIC_TYPES
        resolution_order: list[typing.Type] = list()

        print(classes)

        while len(classes) != 0:
            # TODO resolve circluar / optimise control flow for large N
            current_type = classes.pop(0)

            if current_type not in dependency_map:

                current_field_dependencies = get_dependencies(current_type)
                dependency_map[current_type] = set(utils.flatten_to_list(current_field_dependencies.values()))

            if not dependency_map[current_type].issubset(resolved_dependencies):
                print(dependency_map[current_type], resolved_dependencies)
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
    if issubclass(object_type, enum.Enum):
        [q.put((k, type(v.value))) for k, v in object_type._member_map_.items()]
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

def get_table_contents_from_type(object_type: typing.Type) -> str:
    if issubclass(object_type, enum.Enum):
        # create switch number to different fixed values?
        ...
        return

    prior_tables: list[str] = list()
    subquery = f"CREATE TABLE {object_type.__module__}_{object_type.__name__} (\n"
    table_links: dict[str, str] = {}
    for name, type in typing.get_type_hints(object_type).items():
        # should be abstracted to another method
        # would make the random insertion of union types much easier
        if issubclass(type, Iterable):
            # handle iterable code
            ...

        if issubclass(type, enum.Enum):
            # handle subclass code


def main():
    import modeldata
    get_table_contents_from_type(modeldata.ModelResponse)

if __name__ == "__main__":
    main()
