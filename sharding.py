# -*- coding: utf-8 -*-
"""
    Secret Sharing
    ~~~~~

    :copyright: (c) 2014 by Halfmoon Labs
    :license: MIT, see LICENSE for more details.
"""

import os
import six
from six.moves import range

from binascii import hexlify, unhexlify
from primes import get_large_enough_prime

def random_polynomial(degree, intercept, upper_bound):
    """ Generates a random polynomial with positive coefficients.
    """
    if degree < 0:
        raise ValueError('Degree must be a non-negative number.')
    if upper_bound < 2:
        raise ValueError('Upper bound must be a positive number.')

    coefficients = [intercept]
    for i in range(degree):
        random_coeff = six.integer_types[-1].from_bytes(
            six.binary_type(bytearray(os.urandom(32))), 'big'
        ) % upper_bound
        coefficients.append(random_coeff)
    return coefficients

def get_polynomial_points(coefficients, num_points, upper_bound):
    """ Calculates the first n points on a given polynomial.
    """
    if num_points < 1:
        raise ValueError('Number of points must be a positive number.')

    points = []
    for x in range(1, num_points + 1):
        # start with y = 0
        y = 0
        # add the intercept
        y += coefficients[0]
        # add the remaining terms
        for i in range(1, len(coefficients)):
            y += coefficients[i] * (x**i)
        # wrap the result
        y %= upper_bound
        points.append((x, y))
    return points

def modular_inverse(a, b):
    """ Returns the modular inverse of a with respect to b.
    """
    return pow(a, -1, b)

def lagrange_interpolate(x, points, prime):
    """ Calculates the lagrange basis polynomial for a given set of points.
    """
    # break the points up into lists of x and y values
    x_values, y_values = zip(*points)
    # initialize f(x) and the term counters
    f_x = 0
    # evaluate the lagrange basis polynomial
    for i in range(len(points)):
        # evaluate the numerator
        numerator = 1
        for j in range(len(points)):
            if i == j:
                continue
            numerator *= (x - x_values[j])
        # evaluate the denominator
        denominator = 1
        for j in range(len(points)):
            if i == j:
                continue
            denominator *= (x_values[i] - x_values[j])
        # evaluate the term
        lagrange_polynomial = numerator * modular_inverse(denominator, prime)
        # add the term to f(x)
        f_x += y_values[i] * lagrange_polynomial
    return f_x % prime

class SecretSharer(object):
    """ A secret sharer that can be used to split and recover secrets.
    """
    secret_charset = '0123456789abcdef'

    def __init__(self):
        pass

    @classmethod
    def split_secret(cls, secret_string, share_threshold, num_shares):
        if share_threshold < 2:
            raise ValueError("Share threshold must be >= 2.")
        if share_threshold > num_shares:
            raise ValueError("Share threshold must be less than or equal to the number of shares.")
        if not all(c in cls.secret_charset for c in secret_string):
            raise ValueError("Secret string must be in the character set %s" % cls.secret_charset)

        secret_int = int(secret_string, 16)
        prime = get_large_enough_prime([secret_int, num_shares])
        if not prime:
            raise Exception("Could not find a prime number large enough to accommodate the secret. Please report this issue.")

        coefficients = random_polynomial(share_threshold - 1, secret_int, prime)
        points = get_polynomial_points(coefficients, num_shares, prime)

        shares = []
        for point in points:
            shares.append(hex(point[0])[2:] + '-' + hex(point[1])[2:])
        return shares

    @classmethod
    def recover_secret(cls, shares):
        if not isinstance(shares, list) or len(shares) < 2:
            raise ValueError("Shares must be a list of at least two shares.")

        for share in shares:
            if not isinstance(share, str) or '-' not in share:
                raise ValueError("Each share must be a string of the format 'x-y'.")

        points = []
        for share in shares:
            x, y = share.split('-')
            points.append((int(x, 16), int(y, 16)))

        prime = get_large_enough_prime([p[1] for p in points])
        if not prime:
            raise Exception("Could not find a prime number large enough to accommodate the secret. Please report this issue.")

        free_coefficient = lagrange_interpolate(0, points, prime)
        secret_hex = hex(free_coefficient)[2:]
        return secret_hex

class PlaintextToHexSecretSharer(SecretSharer):
    """ A secret sharer that works with plaintext and produces hex shares.
    """
    secret_charset = '0123456789abcdef'

    def __init__(self):
        pass

    @classmethod
    def split_secret(cls, secret_string, share_threshold, num_shares):
        secret_hex = hexlify(secret_string.encode('utf-8')).decode('utf-8')
        return super(PlaintextToHexSecretSharer, cls).split_secret(
            secret_hex, share_threshold, num_shares
        )

    @classmethod
    def recover_secret(cls, shares):
        secret_hex = super(PlaintextToHexSecretSharer, cls).recover_secret(shares)
        return unhexlify(secret_hex).decode('utf-8')

def create_shards(data: bytes, num_backends: int, threshold: int) -> list[str]:
    """
    Splits data into a number of shards using Shamir's Secret Sharing.

    Args:
        data: The data to be split.
        num_backends: The number of shards to create.
        threshold: The number of shards required to reconstruct the data.

    Returns:
        A list of shards.
    """
    sharer = PlaintextToHexSecretSharer()
    shards = sharer.split_secret(data.hex(), threshold, num_backends)
    return shards

def reconstruct_from_shards(shards: list[str]) -> bytes:
    """
    Reconstructs the original data from a list of shards.

    Args:
        shards: A list of shards.

    Returns:
        The reconstructed data.
    """
    sharer = PlaintextToHexSecretSharer()
    secret_hex = sharer.recover_secret(shards)
    return bytes.fromhex(secret_hex)
