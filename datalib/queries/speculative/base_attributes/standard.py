from datalib.utils.const import BASIC_TYPES
from datalib.utils.type_processing import FunctionParameterSignature
from datalib.queries.speculative.condition_specifier import AccessMethod
from datalib.queries.speculative.condition_validator import \
    RootTable, AbstractAttribute, AbstractAttributeTypeManager, \
    DatatypeConverter, AttributeDetails, AttributeCollection

class StandardRootTable(RootTable):
    ...

class FieldAttribute(AbstractAttribute):
    ...

class FieldTypeAttribute(AbstractAttribute):
    def get_item_by_name(self, args: str) -> AttributeDetails:
        self.attribute_type
        ...

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
                [FieldAttribute(
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