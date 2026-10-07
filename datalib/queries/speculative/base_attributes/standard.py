import typing
from typing import Optional
from types import UnionType, GenericAlias

from datalib.utils.const import BASIC_TYPES, BASIC_TYPE_HINT
from datalib.utils.type_processing import FunctionParameterSignature
from datalib.queries.speculative.condition_specifier import AccessMethod
from datalib.queries.speculative.condition_validator import \
    RootTable, AbstractAttribute, AbstractAttributeTypeManager, \
    DatatypeConverter, AttributeDetails, AttributeCollection

class StandardRootTable(RootTable):
    ...

class FieldSimpleAttribute(AbstractAttribute):
    """
    Represents a field attribute that holds data instead of another reference
    """
    attribute_type: BASIC_TYPE_HINT

class FieldTypeAttribute(AbstractAttribute):
    """
    Represents a field attribute that is another type
    """
    attribute_type: type

    def __init__(self,
                 name: str,
                 attribute_type: type,
                 parent: "Optional[AbstractAttribute]",
                 datatype_converter: "DatatypeConverter"):
        super().__init__(name, attribute_type, parent, datatype_converter)

    def get_item_by_name(self, name: str) -> AttributeDetails:
        own_hints: dict[str, object] = typing.get_type_hints(self.attribute_type)

        if name in own_hints:
            return AttributeDetails(name, [own_hints[name]])

        return AttributeDetails(name, list())

    def get_item_by_type(self, type_: type):
        if self.attribute_type == type_:
            return AttributeDetails(self.name, [self.attribute_type])

        return AttributeDetails(self.name, list())

    def get_item_by_name_and_type(self, name_and_type: tuple[str, type]):
        # this mayyyyyy be an issue, i'm not sure if its possible to specify this abstractly????
        # oh wait no nevermind
        # TODO verify that this implementation is satisfactory
        name, type_ = name_and_type

        own_hints: dict[str, object] = typing.get_type_hints(self.attribute_type)

        if name not in own_hints:
            return AttributeDetails(name, list())

        field_hint: object = own_hints[name]

        if isinstance(field_hint, type):
            if field_hint == type_:
                return AttributeDetails(name, [type_])
            else:
                return AttributeDetails(name, list())

        if isinstance(field_hint, UnionType):
            if type_ in typing.get_args(field_hint):
                return AttributeDetails(name, [type_])

        return AttributeDetails(name, list())

FieldTypeAttribute.register_specialisation(AccessMethod.GETITEM, FieldTypeAttribute.get_item_by_name)
FieldTypeAttribute.register_specialisation(AccessMethod.GETITEM, FieldTypeAttribute.get_item_by_type)
FieldTypeAttribute.register_specialisation(AccessMethod.GETITEM, FieldTypeAttribute.get_item_by_name_and_type)

StandardRootTable.register_specialisation(AccessMethod.GETITEM, FieldTypeAttribute.get_item_by_name)
StandardRootTable.register_specialisation(AccessMethod.GETITEM, FieldTypeAttribute.get_item_by_type)
StandardRootTable.register_specialisation(AccessMethod.GETITEM, FieldTypeAttribute.get_item_by_name_and_type)


class TypeTypeManager(AbstractAttributeTypeManager[type]):
    basic_types = BASIC_TYPES
    def can_handle(self, obj: object) -> bool:
        return isinstance(obj, type)

    def convert_to_attributes(self,
                              attribute_name: str,
                              obj: type,
                              parent: AbstractAttribute) -> AttributeCollection:
        if obj in TypeTypeManager.basic_types:
            return AttributeCollection(
                [FieldSimpleAttribute(
                    attribute_name,
                    obj,
                    parent,
                    parent.datatype_converter)
                ])

        else:
            return AttributeCollection(
                [
                    FieldTypeAttribute(
                        attribute_name,
                        obj,
                        parent,
                        parent.datatype_converter
                    )
                ]
            )

EXPORTED_TYPE_MANGERS = [TypeTypeManager()]
EXPORTED_ROOT_TYPE = StandardRootTable