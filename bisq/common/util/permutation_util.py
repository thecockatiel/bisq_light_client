from collections.abc import Callable
from typing import TypeVar

from utils.concurrency import AtomicInt
from itertools import permutations


_T = TypeVar("T")
_R = TypeVar("R")


class PermutationUtil:

    @staticmethod
    def find_matching_permutation(
        target_value: _R,
        lst: list[_T],
        predicate: Callable[[_R, list[_T]], bool],
        max_iterations: int,
    ) -> list[_T]:
        if predicate(target_value, lst):
            return lst
        else:
            return PermutationUtil._find_matching_permutation(
                target_value, lst, predicate, AtomicInt(max_iterations)
            )

    @staticmethod
    def _find_matching_permutation(
        target_value: _R,
        lst: list[_T],
        predicate: Callable[[_R, list[_T]], bool],
        max_iterations: AtomicInt,
    ) -> list[_T]:
        for level in range(len(lst)):
            # Test one level at a time
            result = PermutationUtil._check_level(
                target_value, lst, predicate, level, 0, max_iterations
            )
            if result:
                return result
        return []

    @staticmethod
    def _check_level(
        target_value: _R,
        previous_level: list[_T],
        predicate: Callable[[_R, list[_T]], bool],
        level: int,
        permutation_index: int,
        max_iterations: AtomicInt,
    ) -> list[_T]:
        if len(previous_level) == 1:
            return []
        for i in range(permutation_index, len(previous_level)):
            if max_iterations.get() <= 0:
                return []
            new_list = previous_level[:i] + previous_level[i + 1 :]
            if level == 0:
                max_iterations.decrement_and_get()
                # Check all permutations on this level
                if predicate(target_value, new_list):
                    return new_list
            else:
                # Test next level
                result = PermutationUtil._check_level(
                    target_value, new_list, predicate, level - 1, i, max_iterations
                )
                if result:
                    return result
        return []
