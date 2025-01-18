"""
A read/write library for length-delimited protobuf messages
Taken from https://github.com/soulmachine/delimited-protobuf
License: Apache-2.0 license
"""
# With edits to make it use asyncio streams

from __future__ import absolute_import

from asyncio import StreamReader, StreamWriter
from typing import BinaryIO, Optional, Type, TypeVar

from google.protobuf.internal.decoder import _DecodeVarint
from google.protobuf.internal.encoder import _EncodeVarint
from google.protobuf.message import Message

T = TypeVar('YourProtoClass', bound=Message)


def _read_varint(stream: BinaryIO, offset: int = 0) -> int:
    """Read a varint from the stream."""
    if offset > 0:
        stream.seek(offset)
    buf: bytes = stream.read(1)
    if buf == b'':
        return 0  # reached EOF
    while (buf[-1] & 0x80) >> 7 == 1:  # while the MSB is 1
        new_byte = stream.read(1)
        if new_byte == b'':
            raise EOFError('unexpected EOF')
        buf += new_byte
    varint, _ = _DecodeVarint(buf, 0)
    return varint

async def _read_varint_async(stream: StreamReader, offset: int = 0) -> int:
    """Read a varint from the stream."""
    if offset > 0:
        await stream.readexactly(offset)
    buf: bytes = await stream.readexactly(1)
    if buf == b'':
        return 0  # reached EOF
    while (buf[-1] & 0x80) >> 7 == 1:  # while the MSB is 1
        new_byte = await stream.readexactly(1)
        if new_byte == b'':
            raise EOFError('unexpected EOF')
        buf += new_byte
    varint, _ = _DecodeVarint(buf, 0)
    return varint


def read_delimited(stream: BinaryIO, proto_class_name: Type[T]) -> Optional[T]:
    """
    Read a single length-delimited message from the given stream.

    Similar to:
      * [`CodedInputStream`](https://github.com/protocolbuffers/protobuf/blob/master/src/google/protobuf/io/coded_stream.h#L66)
      * [`parseDelimitedFrom()`](https://github.com/protocolbuffers/protobuf/blob/master/java/core/src/main/java/com/google/protobuf/Parser.java)
    """
    size = _read_varint(stream)
    if size == 0:
        return None
    buf = stream.read(size)
    msg = proto_class_name()
    msg.ParseFromString(buf)
    return msg

async def read_stream(reader: StreamReader, size: int = -1):
    if size == -1:
        size = 1024
    else:
        size = min(size, 1024)
    buffer = bytearray()
    while True:
        chunk = await reader.read(size)
        if not chunk:  # EOF reached
            break
        buffer.extend(chunk)
    return bytes(buffer)

async def read_delimited_async(stream: StreamReader, proto_class_name: Type[T]) -> Optional[T]:
    """
    Read a single length-delimited message from the given stream.

    Similar to:
      * [`CodedInputStream`](https://github.com/protocolbuffers/protobuf/blob/master/src/google/protobuf/io/coded_stream.h#L66)
      * [`parseDelimitedFrom()`](https://github.com/protocolbuffers/protobuf/blob/master/java/core/src/main/java/com/google/protobuf/Parser.java)
    """
    size = await _read_varint_async(stream)
    if size == 0:
        return None
    buf = await read_stream(stream, size)
    msg = proto_class_name()
    msg.ParseFromString(buf)
    return msg


def write_delimited(stream: BinaryIO, msg: T):
    """
    Write a single length-delimited message to the given stream.

    Similar to:
      * [`CodedOutputStream`](https://github.com/protocolbuffers/protobuf/blob/master/src/google/protobuf/io/coded_stream.h#L47)
      * [`MessageLite#writeDelimitedTo`](https://github.com/protocolbuffers/protobuf/blob/master/java/core/src/main/java/com/google/protobuf/MessageLite.java#L126)
    """
    assert stream is not None
    _EncodeVarint(stream.write, msg.ByteSize())
    stream.write(msg.SerializeToString())