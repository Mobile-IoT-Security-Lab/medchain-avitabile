import sys
import os
import unittest
from unittest.mock import patch

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

        # Assign roles to nodes as in Main.py
        if hasattr(p, 'NODE_ROLES'):
            for node in p.NODES:
                if node.id in p.NODE_ROLES:
                    node.update_role(p.NODE_ROLES[node.id])

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

    def test_redaction_voting_approves_and_executes_delete(self):
        # Fresh state with a tx at index 1
        self.setUp()

        # Choose an admin as requester to have REDACT permission
        requester = p.NODES[0]
        # Sanity: ensure requester has a block and tx at same index
        self.assertGreaterEqual(len(requester.blockchain), 2)
        self.assertGreaterEqual(len(requester.blockchain[self.block_index].transactions), 1)

        # Create a redaction request to DELETE the tx
        req_id = requester.request_redaction(
            target_block=self.block_index,
            target_tx=self.tx_index,
            redaction_type="DELETE",
            reason="test"
        )
        # Locate the request dict
        request = next(r for r in requester.redaction_requests if r["request_id"] == req_id)

        votes_needed = getattr(p, 'minRedactionApprovals', 2)

        # Force deterministic voting: enough voters and all approve
        with patch('random.randint', return_value=votes_needed), \
             patch('random.random', return_value=0.0):
            BlockCommit.process_redaction_voting(block=None, miner=self.miner, event_time=0)

        # Should be approved and executed (tx deleted)
        self.assertEqual(request["status"], "APPROVED")
        self.assertEqual(len(requester.blockchain[self.block_index].transactions), 0)

    def test_redaction_voting_rejects_when_quorum_unreachable(self):
        # Fresh state with a tx at index 1
        self.setUp()

        requester = p.NODES[0]  # ADMIN by config in testing mode
        req_id = requester.request_redaction(
            target_block=self.block_index,
            target_tx=self.tx_index,
            redaction_type="DELETE",
            reason="test-reject"
        )
        request = next(r for r in requester.redaction_requests if r["request_id"] == req_id)

        # Compute authorized voters as in implementation
        authorized_voters = [
            node for node in p.NODES
            if p.NODE_ROLES.get(node.id, "USER") in ["ADMIN", "REGULATOR"]
        ]

        # Temporarily require impossible quorum: more than available voters
        original_quorum = getattr(p, 'minRedactionApprovals', 2)
        p.minRedactionApprovals = len(authorized_voters) + 1

        try:
            # Patch randint to return upper bound to avoid ValueError when lower > upper
            with patch('random.randint', side_effect=lambda a, b: b), \
                 patch('random.random', return_value=1.0):  # all disapprove
                BlockCommit.process_redaction_voting(block=None, miner=self.miner, event_time=0)

            # Since quorum is impossible, status should be REJECTED
            self.assertEqual(request["status"], "REJECTED")
        finally:
            p.minRedactionApprovals = original_quorum

    def test_redaction_voting_pending_state(self):
        # Fresh state with a tx at index 1
        self.setUp()

        requester = p.NODES[0]  # ADMIN by config in testing mode
        req_id = requester.request_redaction(
            target_block=self.block_index,
            target_tx=self.tx_index,
            redaction_type="DELETE",
            reason="test-pending"
        )
        request = next(r for r in requester.redaction_requests if r["request_id"] == req_id)

        # Ensure quorum is modest
        votes_needed = getattr(p, 'minRedactionApprovals', 2)

        # Force exactly votes_needed voters to participate and all disapprove
        with patch('random.randint', return_value=votes_needed), \
             patch('random.random', return_value=1.0):
            BlockCommit.process_redaction_voting(block=None, miner=self.miner, event_time=0)

        # Should remain pending: not enough approvals, but still possible to reach quorum
        self.assertEqual(request["status"], "PENDING")
        # And the transaction should still be present
        self.assertGreaterEqual(len(requester.blockchain[self.block_index].transactions), 1)


if __name__ == "__main__":
    unittest.main()
