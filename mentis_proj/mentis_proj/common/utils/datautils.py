import re
from itertools import islice


def nested_path_get(obj, path_str, strict=True, mode='GET', default_return_value=None):
    """ gets value from an object though a provided path string

    Args:
        obj (obj) : The object containing the data
        path_str ( str) : Dotted path to the target, e.g. mykey.mysecondary_key.my_tertiarykey
        strict (bool) : If True, method will throw an exception if no value exists at the provided
                        path i.e. the path is invalid. Else, the method returns None if there
                        is no value at provided path
        mode (str): the function used to fetch path_str.('POP' or 'GET')
        default_return_value (anything): default return value

    Returns:
        Value at the provided nested path

    Examples:
        >>> obj = { 'success':True,'data':{ 'rank':'student','age':20 }}
        >>> nested_path_get(obj,'data.rank')
        'student'
        >>> nested_path_get(obj,'data.profession', strict=False)
        # Returns None
        >>> nested_path_get(obj,'data.profession', strict=True)
        # raises exception

    """
    nested_keys = path_str.split(".")
    for index, key in enumerate(nested_keys):
        if re.match(r'^[-\w|]+(\.[-\w|]+)?(\.[-\w|]+)?(\.[-\w|]+)?$', key) is None:
            raise Exception(f"{key} is invalid path str")

        try:
            if mode == "POP" and index == len(nested_keys) - 1:
                # if pop is required, pop object at last nested key level
                obj = obj.pop(key, default_return_value)
            else:
                obj = obj[key]
        except Exception:
            if strict is True:
                raise
            else:
                return default_return_value
    return obj


def iteration_grouper(iterable, n, chunk_type=tuple):
    """Yields chunks of any iterable .e.g 5 chunks of size 20 each for a 100 length iterable

    Args:
        iterable : Iterable like dict,list,tuple etc
        n (int): size of each chunk
        chunk_type ( Optional[type]) : Type of chunk to be returned, default is tuple

    Yields: Cchunk of required size and type

    """
    it = iter(iterable)
    while True:
        chunk = tuple(islice(it, n)) if chunk_type is tuple else chunk_type(islice(it, n))
        if not chunk:
            return
        yield chunk
