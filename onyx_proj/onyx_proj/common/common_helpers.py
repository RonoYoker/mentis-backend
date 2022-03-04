import json


def create_dictionary_using_kwargs(**kwargs) -> dict:
    """
    Creates a dictionary using keyword arguments
    """
    response_dict = {}
    for key, value in kwargs.items():
        response_dict[key] = value
    return response_dict
