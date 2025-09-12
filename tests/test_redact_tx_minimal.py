import sys
import os
import unittest

# Ensure project root is on path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from InputsConfig import InputsConfig as p
from Models.Block import Block
from Models.Transaction import Transaction
from Models.Bitcoin.Node import Node as BTCNode
from Models.Bitcoin.BlockCommit import BlockCommit
from Models.Node import Node as BaseNode


class TestRedactTxMinimal(unittest.TestCase):
    def setUp(self):
        # Use testing mode for a smaller, faster network
        p.initialize(testing_mode=True)

        # Ensure all nodes have a genesis block
        BaseNode.generate_genesis_block()

        # Pick a miner node
        self.miner = next(n for n in p.NODES if n.hashPower > 0)

        # Create a minimal block with a single transaction at index 1 for all nodes
        tx = Transaction(
            id=12345,
            sender=self.miner.id,
            to=(self.miner.id + 1) % len(p.NODES),
            value=10,
            tx_type="TRANSFER",
            privacy_level="PUBLIC",
            is_redactable=True,
        )

        # Block for miner and clones for others to avoid shared reference issues
        miner_block = Block(depth=1, id=111, previous=0, miner=self.miner.id, transactions=[tx], r=1)
        self.miner.blockchain.append(miner_block)

        # Make sure other nodes also have a block at same index to avoid IndexError during propagation
        for node in p.NODES:
            if node is self.miner:
                continue
            # Each node needs a block object at index 1
            node.blockchain.append(Block(depth=1, id=miner_block.id, previous=0, miner=self.miner.id, transactions=[tx], r=miner_block.r))

        self.block_index = 1
        self.tx_index = 0

    def test_redact_tx_multisig_path(self):
        # Pre-conditions
        block_before = self.miner.blockchain[self.block_index]
        r_before = block_before.r

        # Execute redaction (should not raise)
        updated_miner = BlockCommit.redact_tx(self.miner, self.block_index, self.tx_index, fee=0.001)

        # Post-conditions
        self.assertIsNotNone(updated_miner)
        block_after = self.miner.blockchain[self.block_index]
        self.assertNotEqual(block_after.r, r_before, "Block randomness should change after redaction")
        self.assertNotEqual(block_after.id, 0, "Block id should be updated after redaction")
        self.assertTrue(len(self.miner.redacted_tx) > 0, "Redaction record should be appended for miner")

    def test_delete_tx_multisig_path(self):
        # Ensure there's one transaction before deletion
        self.assertEqual(len(self.miner.blockchain[self.block_index].transactions), 1)

        # Execute deletion
        updated_miner = BlockCommit.delete_tx(self.miner, self.block_index, self.tx_index)
        self.assertIsNotNone(updated_miner)

        # Miner block no longer has the transaction
        self.assertEqual(len(self.miner.blockchain[self.block_index].transactions), 0)
        # A redaction record should exist
        self.assertTrue(len(self.miner.redacted_tx) > 0)

        # Other nodes should have their block updated too (propagated in delete_tx)
        other = next(n for n in p.NODES if n is not self.miner)
        self.assertEqual(len(other.blockchain[self.block_index].transactions), 0)

    def test_execute_approved_redaction_modify(self):
        # Set up: ensure we have a fresh transaction to modify
        # Reset minimal state
        self.setUp()

        tx_before = self.miner.blockchain[self.block_index].transactions[self.tx_index]
        self.assertNotEqual(getattr(tx_before, 'value', None), "REDACTED")

        request = {
            "request_id": "req-mod",
            "requester": self.miner.id,
            "target_block": self.block_index,
            "target_tx": self.tx_index,
            "redaction_type": "MODIFY",
            "approvals": 2,
        }

        ok = BlockCommit.execute_approved_redaction(request, block=None, event_time=0)
        self.assertTrue(ok)

        tx_after = self.miner.blockchain[self.block_index].transactions[self.tx_index]
        self.assertEqual(tx_after.value, "REDACTED")
        self.assertTrue(tx_after.metadata.get("redacted"))

    def test_execute_approved_redaction_anonymize(self):
        # Set up: fresh state and identifiable sender/to
        self.setUp()
        tx = self.miner.blockchain[self.block_index].transactions[self.tx_index]
        tx.sender = self.miner.id
        tx.to = (self.miner.id + 1) % len(p.NODES)

        request = {
            "request_id": "req-anon",
            "requester": self.miner.id,
            "target_block": self.block_index,
            "target_tx": self.tx_index,
            "redaction_type": "ANONYMIZE",
            "approvals": 2,
        }

        ok = BlockCommit.execute_approved_redaction(request, block=None, event_time=0)
        self.assertTrue(ok)

        tx_after = self.miner.blockchain[self.block_index].transactions[self.tx_index]
        self.assertEqual(tx_after.sender, 0)
        self.assertEqual(tx_after.to, 0)
        self.assertTrue(tx_after.metadata.get("anonymized"))


if __name__ == "__main__":
    unittest.main()
