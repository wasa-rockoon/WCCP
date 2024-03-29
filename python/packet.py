import struct
from enum import Enum
from typing import List, Optional

char = str

class Payload:

    def __init__(self):
        self.buf = b'\x00\x00\x00\x00'

    @property
    def int8(self) -> Optional[int]:
        if len(self.buf) < 1: return None
        return struct.unpack('<b', self.buf)[0]
    @property
    def int16(self) -> Optional[int]:
        if len(self.buf) < 2: return None
        return struct.unpack('<h', self.buf)[0]
    @property
    def int32(self) -> Optional[int]:
        if len(self.buf) < 4: return None
        return struct.unpack('<i', self.buf)[0]
    @property
    def uint8(self) -> Optional[int]:
        if len(self.buf) < 1: return None
        return struct.unpack('<B', self.buf[:1])[0]
    @property
    def uint16(self) -> Optional[int]:
        if len(self.buf) < 2: return None
        return struct.unpack('<H', self.buf)[0]
    @property
    def uint32(self) -> Optional[int]:
        if len(self.buf) < 4: return None
        return struct.unpack('<I', self.buf)[0]
    @property
    def float16(self) -> Optional[float]:
        if len(self.buf) < 2: return None
        return struct.unpack('<e', self.buf)[0]
    @property
    def float32(self) -> Optional[float]:
        if len(self.buf) < 4: return None
        return struct.unpack('<f', self.buf)[0]


class Entry:
    def __init__(self, type, payload):
        self.type = type
        self.payload = payload

    def decode(self, buf: bytes) -> int:
        self.type = chr((buf[0] & 0b00111111) + 64)
        len_code = (buf[0] & 0b11000000) >> 6
        len_ = [0, 1, 2, 4][len_code]
        self.payload.buf = buf[1:1+len_] + b'\x00' * (4 - len_)

        return 1 + len_

    def print(self):
        print(' ', self.type, self.payload.int32,
              '{:.6E}'.format(self.payload.float32),
              self.payload.buf
              )

    def printError(self):
        print(' ', self.type, self.payload.uint8, self.payload.buf[1:])

    def printSanity(self):
        print(' ', self.type, self.payload.uint8, bin(self.payload.uint32 >> 8))


class Kind(Enum):
    COMMAND = 0
    TELEMETRY = 1

    def __str__(self) -> str:
        if self == Kind.COMMAND:
            return 'cmd'
        else:
            return 'tlm'

class Packet:

    def __init__(self, kind: Kind, id: char, from_: int, dest: int,
                 size: int, node: int = 0, seq: int = 0):
        self.id = id
        self.kind = kind
        self.from_ = from_
        self.node = node
        self.size = size
        self.dest = dest
        self.seq = seq
        self.entries: List[Entry] = list(map(lambda _: Entry(None, Payload()),
                                             [None] * size))

    @staticmethod
    def decode(buf: bytes) -> Optional['Packet']:
        kind = Kind(buf[0] >> 7)
        id = chr(buf[0] & 0b01111111)
        from_ = buf[1] >> 5
        node = buf[1] & 0b11111
        dest = buf[2] >> 5;
        size = buf[2] & 0b11111;
        seq  = buf[3];

        packet = Packet(kind, id, from_, dest, size, node, seq)

        i = 4

        for n in range(0, size):
            if i >= len(buf):
                return None
            i += packet.entries[n].decode(buf[i:])

        return packet

    def find(self, entry_type: char, index: int = 0) -> Optional[Entry]:
        i = 0
        for entry in self.entries:
            if entry.type == entry_type:
                if i == index:
                    return entry;
                i += 1
        return None

    def print(self):
        print(f"{self.kind} '{self.id}' {self.from_}.{self.node} -> {self.dest} [{self.size}] #{self.seq}")
        # print(self.kind, self.id, self.from_, self.dest, self.size, self.seq)
        for entry in self.entries:

            if self.id == '!':
                entry.printError()
            elif self.id == '?':
                entry.printSanity()
            else:
                entry.print()
