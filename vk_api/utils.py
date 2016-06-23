import json


def json_to_file(data_dict, file_name):
    """
    Dump python dictionary to json file
    :param data_dict: python dictionary to be dumped
    :type data_dict: dict
    :param file_name: filepath to dump data to
    :type file_name: str
    """
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=4)


def json_from_file(file_name):
    """Read data from file and return as dict,
    if any exception occurs - return empty dict
    :param file_name: filepath to dump data to
    :type file_name: str
    :return: dictionary with data from json file
    :rtype: dict
    """
    data = {}
    with open(file_name, "r", encoding="utf-8") as f_in:
        data = json.load(f_in)
    return data
