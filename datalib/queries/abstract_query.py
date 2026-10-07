from abc import ABCMeta


class Query[QueryType, Datatype](metaclass=ABCMeta):
    ...

class QueryBundle[QueryType, *Datatypes](metaclass=ABCMeta):
    ...