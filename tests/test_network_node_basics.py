#!/usr/bin/env python3
import unittest

from InputsConfig import InputsConfig as p
from Models.Node import Node as BaseNode
import Models.Network as Net
from Models.Block import Block


class TestNetworkNodeBasics(unittest.TestCase):
    def setUp(self):
        p.initialize(testing_mode=True)

    def test_block_and_tx_prop_delays(self):
        d1 = Net.Network.block_prop_delay()
        d2 = Net.Network.tx_prop_delay()
        self.assertIsInstance(d1, float)
        self.assertIsInstance(d2, float)
        self.assertGreaterEqual(d1, 0.0)
        self.assertGreaterEqual(d2, 0.0)

    def test_node_genesis_and_reset(self):
        # Initially, nodes should have empty chains
        self.assertTrue(all(len(n.blockchain) == 0 for n in p.NODES))

        # Generate genesis block for all nodes
        BaseNode.generate_genesis_block()
        self.assertTrue(all(len(n.blockchain) == 1 for n in p.NODES))

        # last_block and blockchain_length on a sample node
        node0 = p.NODES[0]
        self.assertIsInstance(node0.last_block(), Block)
        self.assertEqual(node0.blockchain_length(), 1)

        # Reset state for all nodes
        BaseNode.resetState()
        self.assertTrue(all(len(n.blockchain) == 0 for n in p.NODES))
        self.assertTrue(all(len(n.transactionsPool) == 0 for n in p.NODES))


if __name__ == "__main__":
    unittest.main()
