from abc import ABCMeta


class Query[QueryType, Datatype](metaclass=ABCMeta):
    ...