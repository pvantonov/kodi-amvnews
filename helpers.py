# coding=utf-8
"""
Helpers.
"""
from resources.lib.enum import Enum

__all__ = ['Singleton', 'Language']


class Language(Enum):
    """
    Language enum.
    """
    Unknown = 0
    Russian = 1
    English = 2


class Singleton(type):
    """
    Singleton metaclass.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
