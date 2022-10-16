import bisect
import sys
from typing import List

from pyroaring import BitMap


class Container:
    key: int
    bitmap: BitMap

    def __init__(self, key, bitmap):
        self.key = key
        self.bitmap = bitmap


def keyfunc(entry):
    return entry.key


def split64(n):
    return n >> 32, n & 0xFFFFFFFF


def combine64(key, v):
    return (key << 32) + v


class BitMap64:
    containers: List[Container]

    def __init__(self):
        self.containers = []

    def _container(self, key, create=False):
        "get container or create empty one"
        i = bisect.bisect_left(self.containers, key, key=keyfunc)
        if i >= len(self.containers) or self.containers[i].key != key:
            if not create:
                return None
            self.containers.insert(i, Container(key, BitMap()))
        return self.containers[i]

    def _add_container(self, container):
        i = bisect.bisect_left(self.containers, container.key, key=keyfunc)
        assert i == len(self.containers) or self.containers[i].key != container.key
        self.containers.insert(i, container)

    @classmethod
    def deserialize(cls, buf):
        m64 = cls()

        n = int.from_bytes(buf[:8], "little")
        offset = 8
        for i in range(n):
            key = int.from_bytes(buf[offset : offset + 4], "little")
            offset += 4
            m = BitMap.deserialize(buf[offset:])
            offset += sys.getsizeof(m)

            m64._add_container(Container(key, m))

        return m64

    def serialize(self):
        chunks = [len(self.containers).to_bytes(8, "little")]
        for entry in self.containers:
            chunks.append(entry.key.to_bytes(4, "little"))
            chunks.append(entry.bitmap.serialize())
        return b"".join(chunks)

    def __sizeof__(self):
        return 8 + sum(4 + sys.getsizeof(c) for c in self.containers)

    def __str__(self):
        return str(self.containers)

    def __repr__(self):
        return str(self)

    def __len__(self):
        return sum(len(c.bitmap) for c in self.containers)

    def __bool__(self):
        return bool(self.containers)

    def __contains__(self, n):
        key, v = split64(n)
        c = self._container(key, create=False)
        if c is None:
            return False
        return v in c.bitmap

    def __getitem__(self, n):
        for c in self.containers:
            length = len(c.bitmap)
            if n >= length:
                n -= length
            else:
                v = c.bitmap[n]
                return combine64(c.key, v)

    def __iter__(self):
        for c in self.containers:
            for v in c.bitmap:
                yield combine64(c.key, v)

    def add(self, n):
        key, v = split64(n)
        self._container(key, create=True).bitmap.add(v)

    def add_checked(self, n):
        key, v = split64(n)
        self._container(key, create=True).bitmap.add_checked(v)

    def remove(self, n):
        key, v = split64(n)
        c = self._container(key, create=False)
        if c is not None:
            c.bitmap.discard(v)

    def remove_checked(self, n):
        key, v = split64(n)
        c = self._container(key, create=False)
        if c is None:
            raise KeyError(n)
        try:
            c.remove(v)
        except KeyError:
            raise KeyError(n)

    def min(self):
        if len(self.containers) == 0:
            raise ValueError("Empty roaring64 bitmap, there is no minimum.")
        return self.containers[0].bitmap.min()

    def max(self):
        if len(self.containers) == 0:
            raise ValueError("Empty roaring64 bitmap, there is no maximum.")
        return self.containers[-1].bitmap.max()

    def rank(self, n):
        key, v = split64(n)
        size = 0
        for c in self.containers:
            if c.key > key:
                return size
            elif c.key < key:
                size += len(c.bitmap)
            else:
                return size + c.bitmap.rank(v)
        return size
