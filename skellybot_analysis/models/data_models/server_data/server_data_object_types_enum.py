from enum import Enum


class ServerDataObjectTypes(Enum):
    SERVER = 'server'
    CATEGORY = 'category'
    CHANNEL = 'channel'
    THREAD = 'thread'
    MESSAGE = 'message'
    USER = 'user'
