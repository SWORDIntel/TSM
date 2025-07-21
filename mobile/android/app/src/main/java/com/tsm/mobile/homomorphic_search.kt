package com.tsm.mobile

import java.math.BigInteger
import java.util.*

class Paillier(
    val n: BigInteger,
    val nSquared: BigInteger,
    val g: BigInteger,
    private val lambda: BigInteger,
    private val mu: BigInteger
) {

    fun encrypt(m: BigInteger): BigInteger {
        val r = BigInteger(n.bitLength(), Random()).mod(n)
        return g.modPow(m, nSquared).multiply(r.modPow(n, nSquared)).mod(nSquared)
    }

    fun decrypt(c: BigInteger): BigInteger {
        val u = c.modPow(lambda, nSquared)
        val l = u.subtract(BigInteger.ONE).divide(n)
        return l.multiply(mu).mod(n)
    }

    companion object {
        fun create(): Paillier {
            val bitLength = 512
            val p = BigInteger.probablePrime(bitLength / 2, Random())
            val q = BigInteger.probablePrime(bitLength / 2, Random())
            val n = p.multiply(q)
            val nSquared = n.multiply(n)
            val g = n.add(BigInteger.ONE)
            val lambda = p.subtract(BigInteger.ONE).multiply(q.subtract(BigInteger.ONE))
            val mu = g.modPow(lambda, nSquared).subtract(BigInteger.ONE).divide(n).modInverse(n)
            return Paillier(n, nSquared, g, lambda, mu)
        }
    }
}

class HomomorphicSearchPrototype {

    private val paillier = Paillier.create()

    fun generateEncryptedQuery(term: Int): BigInteger {
        return paillier.encrypt(BigInteger.valueOf(term.toLong()))
    }
}
