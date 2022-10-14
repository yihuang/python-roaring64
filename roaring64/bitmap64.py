import bisect
import sys
from typing import List

import pyroaring

__version__ = "0.1.0"


class Entry:
    key: int
    bitmap: pyroaring.BitMap

    def __init__(self, key, bitmap):
        self.key = key
        self.bitmap = bitmap


class BitMap64:
    entries: List[Entry]

    @classmethod
    def deserialize(cls, buf):
        entries = []

        n = int.from_bytes(buf[:8], "little")
        offset = 8
        for i in range(n):
            key = int.from_bytes(buf[offset : offset + 4], "little")
            offset += 4
            m = pyroaring.BitMap.deserialize(buf[offset:])
            offset += sys.getsizeof(m)

            bisect.insort_right(entries, Entry(key, m), key=lambda o: o.key)

        m64 = cls()
        m64.entries = entries
        return m64

    def serialize(self):
        chunks = [len(self.entries).to_bytes(8, "little")]
        for entry in self.entries:
            chunks.append(entry.key.to_bytes(4, "little"))
            chunks.append(entry.bitmap.serialize())
        return b"".join(chunks)


if __name__ == "__main__":
    buf = b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;0\x00\x00\x01\x00\x003\x00\x01\x00\x01\x003\x00"
    bm64 = BitMap64.deserialize(buf)
    assert bm64.serialize() == buf
