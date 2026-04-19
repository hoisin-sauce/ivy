from typing import Any

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
