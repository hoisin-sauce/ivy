from dataclasses import dataclass
from enum import Enum

class DataEnum(Enum):
    value_1 = 1
    value_2 = 2
    value_3 = 3
    value_4 = "4"

@dataclass
class SampleClass:
    foreign: DataEnum
