from typing import List


def role_name(subject: str, predicate: str, obj: str):
    s = normalize(f'{subject}-{predicate}-{obj}')
    return s[0].lower() + s[1:]


def class_name(name: str):
    s = individual_name(name)
    return s[0].upper() + s[1:]


def individual_name(name: str) -> str:
    name: str = normalize(name)
    if len(name.strip()) == 0:
        return ''
    char_list: List[str] = list(name)
    return ''.join(char_list)


def normalize(value: str) -> str:
    char_list: List[str] = list(value)
    length: int = len(char_list)
    for i in range(1, length):
        if char_list[i - 1] in ['-']:
            char_list[i] = char_list[i].upper()
    return ''.join(char_list).replace('-', '')


def prefix(value: str):
    return ':'.join(value.split(':')[:-1])


def suffix(value: str):
    return value.split(':')[-1]
