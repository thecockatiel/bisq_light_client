from typing import Iterable, Iterator, TypeVar, Generic

T = TypeVar("T")


class UniqueIterator(Generic[T]):
    def __init__(self, iterator: Iterator[T]):
        self._iterator = iterator
        self._seen: set[T] = set()

    def __iter__(self) -> Iterator[T]:
        return self

    def __next__(self) -> T:
        while True:
            item = next(self._iterator)
            if item not in self._seen:
                self._seen.add(item)
                return item


def distinct_iterator(iterator: Iterator[T]) -> Iterator[T]:
    return UniqueIterator(iterator)


def not_none_iterator(iterable: Iterable[T]) -> Iterator[T]:
    """Returns an iterator that filters out None values from the input iterable"""
    return filter(lambda x: x is not None, iterable)


def is_iterable(obj):
    try:
        iter(obj)
        return True
    except:
        return False
