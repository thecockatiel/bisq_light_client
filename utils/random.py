
import random

__random_int_min_range = -(2**31)
__random_int_max_range = 2**31 - 1

def next_random_int():
    return random.randint(__random_int_min_range, __random_int_max_range)
