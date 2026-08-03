from abc import ABCMeta, abstractmethod

class DatabaseConstraint(metaclass=ABCMeta):
    @abstractmethod
    def __repr__(self) -> str:
        ...

class FieldConstraint(DatabaseConstraint, metaclass=ABCMeta):
    ...

class TableConstraint(DatabaseConstraint, metaclass=ABCMeta):
    ...