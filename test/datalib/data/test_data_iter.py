from dataclasses import dataclass

@dataclass
class ExampleTable:
    iterable_field: list[int]
    dictionary_field: dict[int, str]

