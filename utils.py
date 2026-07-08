from itertools import chain
from typing import Any, Callable, Iterable
import queue
import threading
import typing

def safe_is_subclass(obj: Any, class_or_tuple: typing.Type|tuple[typing.Type]) -> bool:
    return isinstance(obj, type) and issubclass(object, class_or_tuple)

def flatten_to_list[T](lst: Iterable[Iterable[T]]) -> list[T]:
    return list(chain(*lst))

def public_dir(obj: Any) -> list[str]:
    return [i for i in dir(obj) if not i.startswith("__")]

def object_to_dict(obj: Any) -> dict | Any:
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
    def __init__(self, input_obj: A):
        self.val = input_obj
        self.queue = queue.Queue()

    def get_input(self) -> A:
        return self.val

    def put_output(self, output_obj: B):
        self.queue.put(output_obj)

    def get_output(self) -> B:
        return self.queue.get()

class Scheduler[A, B]:
    process: Callable[[A], B]
    request_queue: queue.Queue[Request[A, B]] = queue.Queue()

    def __post_init__(self):
        threading.Thread(target=self.process_loop, daemon=True).start()

    def process_loop(self):
        while True:
            obj: Request[A, B] = self.request_queue.get()
            obj.put_output(self.process(obj.get_input()))
