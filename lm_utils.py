"""Generic utility functions, may be refactored into multiple files later on.
"""
from itertools import chain
from typing import Any, Callable, Iterable
import queue
import threading
import typing

def safe_is_subclass(obj: Any, class_or_tuple: typing.Type|tuple[typing.Type]) -> bool:
    """
    Safe version of is_subclass for an unknown datatype, does not raise an
    exception if the object is not a type.
    Args:
        obj
            The object to be checked
        class_or_tuple
            A class or tuple of classes to be checked
    Returns:
        Boolean representing if the object is a subclass of the
        provided class or one of the classes in the provided tuple
    """
    return isinstance(obj, type) and issubclass(obj, class_or_tuple)

def flatten_to_list[T](two_d_iterable: Iterable[Iterable[T]]) -> list[T]:
    """
    Flattens 2-dimesional iterable into a list.
    Args:
        two_d_iterable:
            Second dimensional iterable to be flattened
    Returns:
        List containing the flattened iterable
    """
    return list(chain(*two_d_iterable))

def flatten_to_set[T](two_d_iterable: Iterable[Iterable[T]]) -> set[T]:
    """
        Flattens 2-dimesional iterable into a set.
        Args:
            two_d_iterable:
                Second dimensional iterable to be flattened
        Returns:
            Set containing the flattened iterable
        """
    return set(chain(*two_d_iterable))

def public_dir(obj: Any) -> list[str]:
    """
    Returns a list of the public attributes in the provided object.
    Args:
        obj
            Object to be processed
    Returns:
        List containing the public attributes in the provided object
    """
    return [i for i in dir(obj) if not i.startswith("__")]

def object_to_dict(obj: Any) -> dict | Any:
    """
    Converts the provided object to a dictionary.
    Args:
        obj
            Object to be processed
    Returns:
        Dictionary representation of the object
    """
    if isinstance(obj, (list, tuple)):
        return [object_to_dict(i) for i in obj]

    if not '__dict__' in dir(obj):
        return obj

    obj_dict: dict = obj.__dict__
    ret_dict = {}
    for k, v in obj_dict.items():
        if v is not None:
            ret_dict[k] = object_to_dict(v)

    return ret_dict

class Request[A, B]:
    """
    Object representing an asynchronous request with data of type A for data of type B
    """
    def __init__(self, input_obj: A):
        self.val = input_obj
        self.queue = queue.Queue()

    def get_input(self) -> A:
        """
        Returns the input value provided
        Returns:
            Input value provided when the request was made
        """
        return self.val

    def put_output(self, output_obj: B) -> None:
        """
        Places the output value into the object
        Args:
            output_obj:
                Object to be returned to the request maker
        """
        self.queue.put(output_obj)

    def get_output(self) -> B:
        """
        Retrieve the output value provided asynchronously
        Returns:
            Object provided to the request after it has been processed
        """
        return self.queue.get()

class Scheduler[A, B]:
    """
    Object representing a scheduler to process requests of type [A, B]

    Attributes:
        process: Process to be called on the input data
        request_queue: Queue of requests to be processed
    """
    process: Callable[[A], B]
    request_queue: queue.Queue[Request[A, B]] = queue.Queue()

    def __post_init__(self) -> None:
        """
        Initialises the thread managing the scheduler as a daemon
        """
        threading.Thread(target=self.process_loop, daemon=True).start()

    def process_loop(self) -> None:
        """
        Processes the requests provided by the scheduler.
        Calls self.post_processing with the input value and output value
        to provide functionality to subclasses.
        """
        while True:
            obj: Request[A, B] = self.request_queue.get()

            input_value: A = obj.get_input()
            processed_value: B = self.process(obj)

            obj.put_output(processed_value)

            self.post_processing(input_value, processed_value)

    def process_object(self, obj: A) -> B:
        """
        Queue object for processing
        Args:
            obj
                Object to be processed
        Returns:
            The processed object

            Will halt execution until the scheduler processes the object
        """
        request: Request[A, B] = Request(obj)
        self.request_queue.put(request)
        return request.get_output()

    def post_processing(self, input_value: A, output_value: B) -> None:
        """
        Any necessary post-processing to be executed after an object is processed.

        Does nothing at base. Designed for easy overwriting.
        Args:
            input_value
                The input object that has been processed
            output_value
                The output object from that processing
        Returns:
            Nothing
        """
        ...
