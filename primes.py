# -*- coding: utf-8 -*-
"""
    Secret Sharing
    ~~~~~

    :copyright: (c) 2014 by Halfmoon Labs
    :license: MIT, see LICENSE for more details.
"""

import six
from six.moves import range

def get_large_enough_prime(batch):
    """ Return a prime number that is greater than all the numbers in the list.
    """
    # build a list of all the numbers in the batch
    numbers = []
    for num in batch:
        if isinstance(num, list):
            numbers += get_large_enough_prime(num)
        else:
            numbers.append(num)
    # return a prime that is greater than all the numbers in the list
    largest_number = max(numbers)
    for prime in mersenne_primes:
        if prime > largest_number:
            return prime
    return None

def calculate_mersenne_primes():
    """
    Returns a list of Mersenne primes that are smaller than 2^521 + 1
    """
    mersenne_prime_exponents = [
        2, 3, 5, 7, 13, 17, 19, 31, 61, 89, 107, 127, 521
    ]
    primes = []
    for exp in mersenne_prime_exponents:
        prime = int(1)
        for i in range(exp):
            prime = prime * 2
        prime = prime - 1
        primes.append(prime)
    return primes

mersenne_primes = calculate_mersenne_primes()
