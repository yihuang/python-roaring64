from roaring64 import BitMap64


def test_serialization():
    buf = (
        b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00;0\x00\x00\x01"
        b"\x00\x003\x00\x01\x00\x01\x003\x00"
    )
    bm64 = BitMap64.deserialize(buf)
    assert bm64.serialize() == buf
    assert len(bm64) > 0

    # multiple containers
    m = BitMap64()
    m.add(1)
    m.add(2**33)
    m.add(2**33 + 10)
    m.add(2**34)
    bm64 = BitMap64.deserialize(m.serialize())
    assert len(bm64) == 4
    assert list(m) == [1, 2**33, 2**33 + 10, 2**34]


def test_map32():
    m = BitMap64()
    m.add(1)
    assert 1 in m
    assert 10 not in m
    m.add(10)
    assert 10 in m
    assert len(m) == 2
    assert m[0] == 1
    assert m[1] == 10

    assert m.min() == 1
    assert m.max() == 10

    m.remove(1)
    assert len(m) == 1
    assert 1 not in m
    assert m.min() == m.max() == 10

    for i in range(100, 200):
        m.add(i)
    assert m.max() == 199


def test_map64():
    m = BitMap64()
    m.add(1)
    m.add(2**33)
    m.add(2**33 + 10)
    m.add(2**34)
    assert len(m) == 4
    assert m[0] == 1
    assert m[1] == 2**33
    assert m[2] == 2**33 + 10
    assert m[3] == 2**34
    assert list(m) == [1, 2**33, 2**33 + 10, 2**34]


def test_rank():
    m = BitMap64()
    m.add(1)
    m.add(2**33)
    m.add(2**33 + 10)
    m.add(2**34)

    assert 1 == m.rank(1)
    assert 1 == m.rank(2)
    assert 1 == m.rank(2**32)
    assert 2 == m.rank(2**33)
    assert 4 == m.rank(2**34)
