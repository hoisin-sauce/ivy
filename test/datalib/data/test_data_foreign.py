from dataclasses import dataclass
from typing import Optional

@dataclass
class OptionalField:
    integer: Optional[int]
    string: Optional[str]
    boolean: Optional[bool]
    foreign: Optional["ExampleForeign"]

@dataclass
class ExampleForeign:
    data: str