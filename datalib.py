import enum
import typing
import types
import utils
import queue
import const
from collections.abc import Iterable, Sequence
from const import SQLFields, SQLFieldDefaults


class Database:
    def __init__(self, modules: list[types.ModuleType]):
        classes: list[typing.Type] = \
            utils.flatten_to_list([get_classes_from_module(i) for i in modules])

        self.dependency_map: dict[typing.Type, set[typing.Type]] = {}
        resolved_dependencies: set[typing.Type] = const.BASIC_TYPES
        resolution_order: list[typing.Type] = list()

        print(classes)

        while len(classes) != 0:
            # TODO resolve circluar / optimise control flow for large N
            current_type = classes.pop(0)

            if current_type not in self.dependency_map:

                current_field_dependencies = get_dependencies(current_type)
                self.dependency_map[current_type] = set(utils.flatten_to_list(current_field_dependencies.values()))

            if not self.dependency_map[current_type].issubset(resolved_dependencies):
                print(self.dependency_map[current_type], resolved_dependencies)
                [classes.append(i) for i in self.dependency_map[current_type]-resolved_dependencies if i not in classes]
                classes.append(current_type)
                continue

            # we can now actually place it in order
            resolution_order.append(current_type)
            resolved_dependencies.add(current_type)

        print(resolution_order)
        self.resolved_classes = set(resolution_order)


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

def get_table_contents_from_type(self, object_type: typing.Type) -> str:
    pre_tables: list[str] = list()
    table_name = f"{object_type.__module__}_{object_type.__name__}"
    subquery = f"CREATE TABLE {table_name} (\n"
    table_links: dict[str, str] = {}

    if issubclass(object_type, enum.Enum):
        # create switch number to different fixed values?
        # create a table with fixed rows in it pointing to the current values
        # i.e. as a lookup table
        # then we store the actual values

        lookup_table_name = table_name + "_enum_"

        lookup_table_fields = {
            lookup_table_name + "_id": SQLFieldDefaults.PRIMARY_KEY_CONSTRUCTOR,

        }

        # how do we manage to deal with different typing?
        # should we also handle custom objects within enums?
        if len(dependencies := self.dependency_map[object_type]) == 1:  # foreign types
            # we can just store the value in one database
            dependencies: set[typing.Type]

            enum_field_type = dependencies.pop()
            assert enum_field_type in const.BASIC_TYPES, "Enums should only hold basic values"
        else:
            # TODO multi table switching
            raise NotImplemented("Enums can only hold one datatype")
            # we need to manage storing multiple different datatypes here
            ...
        return ""



    for field_name, type in typing.get_type_hints(object_type).items():
        # should be abstracted to another method
        # would make the random insertion of union types much easier
        if issubclass(type, Iterable):
            # handle iterable code

            # create a table linking to current table id and iterator id
            # iterator id is a table holding the contents
            # e.g. for a list[str]
            # we create table fieldname
            # with tablename id and resolve the str field to str

            # how do we avoid name collisions here
            # make the iterator field depend on something like

            iterator_table_name = table_name + "_iter_" + field_name

            iterator_table_fields = {
                iterator_table_name + "_id": SQLFieldDefaults.PRIMARY_KEY_CONSTRUCTOR
            }

            if issubclass(type, Sequence):
                iterator_table_fields["position"] = SQLFieldDefaults.ORDERING_FIELD

            # We now need to point to the datatype inside the iterable object
            ...

        if issubclass(type, enum.Enum):

            ...


def main():
    import modeldata
    get_table_contents_from_type(modeldata.ModelResponse)

if __name__ == "__main__":
    main()

# TODO manage migration/ changing datastructures, e.g. matching like tables
