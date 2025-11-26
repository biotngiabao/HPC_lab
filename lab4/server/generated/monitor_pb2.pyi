from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class CommandRequest(_message.Message):
    __slots__ = ("command",)
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    command: str
    def __init__(self, command: _Optional[str] = ...) -> None: ...

class CommandResponse(_message.Message):
    __slots__ = ("timestamp", "hostname", "metric", "value")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    HOSTNAME_FIELD_NUMBER: _ClassVar[int]
    METRIC_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    timestamp: str
    hostname: str
    metric: str
    value: str
    def __init__(self, timestamp: _Optional[str] = ..., hostname: _Optional[str] = ..., metric: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
