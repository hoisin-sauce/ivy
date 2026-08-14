class SampleChild:
    a: int
    b: str
    c: bool

class SampleParent:
    some_field: str
    child: SampleChild

class SomeContainer:
    some_children: list[SampleChild]
    some_parent_as_a_child: SampleParent
    some_other_field: str

class SampleGrandparent:
    parent: SampleParent
    child: SampleChild

class SampleGreatGrandparent:
    grandparent: SampleGrandparent

class CouldHaveParentOrGrandparent:
    parent_or_grandparent: SampleParent | SampleChild
    simpler_concept: int | str | bool