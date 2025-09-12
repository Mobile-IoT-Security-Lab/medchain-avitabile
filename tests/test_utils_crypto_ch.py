#!/usr/bin/env python3
import unittest

from CH.HashUtil import quickPower, exgcd, str2int
from CH.SecretSharing import split, recover_split, make_random_shares, recover_secret, secret_share


class TestCryptoUtilsCH(unittest.TestCase):
    def test_quick_power(self):
        # 2^5 mod 13 == 6
        self.assertEqual(quickPower(2, 5, 13), 6)

    def test_exgcd(self):
        a, b = 240, 46
        x, y, g = exgcd(a, b)
        self.assertEqual(g, 2)
        self.assertEqual(a * x + b * y, g)

    def test_str2int_stability(self):
        h1 = str2int("hello")
        h2 = str2int("hello")
        h3 = str2int("world")
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h3)

    def test_secret_splitting_and_recovery(self):
        # Use a deterministic small secret for the unit test
        secret = 12345678901234567890
        s1, s2 = split(secret)
        self.assertIsInstance(s1, int)
        self.assertIsInstance(s2, int)
        recovered = recover_split(s1, s2)
        self.assertEqual(recovered, secret)

    def test_shamir_sharing(self):
        secret = 987654321
        shares = make_random_shares(secret, minimum=3, shares=5)
        self.assertEqual(len(shares), 5)
        # Recover with any 3 shares
        rec = recover_secret(shares[:3])
        self.assertEqual(rec, secret)

    def test_secret_share_function_runs(self):
        # Just ensure it runs and returns an int
        secret = 1122334455
        result = secret_share(secret, minimum=2, shares=3)
        self.assertIsInstance(result, int)


if __name__ == "__main__":
    unittest.main()
