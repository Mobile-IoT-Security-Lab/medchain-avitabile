#!/usr/bin/env python3
import unittest

from InputsConfig import InputsConfig as p
from Models.Transaction import LightTransaction, Transaction
from Models.Node import Node as BaseNode


class TestLightTransactions(unittest.TestCase):
    def setUp(self):
        p.initialize(testing_mode=True)
        # Reduce generation for a fast test
        p.Tn = 1
        p.Binterval = 2
        BaseNode.generate_genesis_block()

    def test_create_and_execute_transactions(self):
        # Create a small pool
        LightTransaction.create_transactions()
        self.assertGreaterEqual(len(LightTransaction.pending_transactions), 1)
        # Execute selection
        txs, size = LightTransaction.execute_transactions()
        self.assertIsInstance(txs, list)
        self.assertIsInstance(size, float)
        # Sanity checks on selected transactions
        for tx in txs:
            self.assertIsInstance(tx, Transaction)
            self.assertIn(tx.tx_type, {"TRANSFER", "CONTRACT_CALL", "CONTRACT_DEPLOY", "REDACTION_REQUEST"})


if __name__ == "__main__":
    unittest.main()
