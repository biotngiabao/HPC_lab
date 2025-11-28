from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class CommandRequest(_message.Message):
    __slots__ = ("commandList",)
    COMMANDLIST_FIELD_NUMBER: _ClassVar[int]
    commandList: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, commandList: _Optional[_Iterable[str]] = ...) -> None: ...

class CommandResponse(_message.Message):
    __slots__ = ("timestamp", "hostname", "metric", "value", "unit")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    HOSTNAME_FIELD_NUMBER: _ClassVar[int]
    METRIC_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    UNIT_FIELD_NUMBER: _ClassVar[int]
    timestamp: str
    hostname: str
    metric: str
    value: str
    unit: str
    def __init__(self, timestamp: _Optional[str] = ..., hostname: _Optional[str] = ..., metric: _Optional[str] = ..., value: _Optional[str] = ..., unit: _Optional[str] = ...) -> None: ...
