#!/usr/bin/env python3
"""
Redactable Blockchain Demo (Ateniese et al.)
===========================================

This demo illustrates the core idea from the paper
"Redactable Blockchain – or – Rewriting History in Bitcoin and Friends":

- Blocks commit to their contents using a chameleon hash.
- With the trapdoor, it is possible to change a block's contents and
  adjust the randomness r to keep the block hash unchanged.
- The hash chain remains valid, so the chain does not need to be rebuilt.

We build a tiny chain, perform a redaction on an interior block, and
verify that the block id (hash) remains stable while the contents change.
"""

from __future__ import annotations

import sys
import os
import hashlib
import json
import random
from dataclasses import dataclass, field
from typing import List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from CH.ChameleonHash import q, PK, chameleonHash, forge


def msg_for_block(txs: List[int], previous: int) -> str:
    """Compute the message m that the block commits to (tx ids + previous)."""
    x = json.dumps([txs, previous], sort_keys=True).encode()
    return hashlib.sha256(x).hexdigest()


@dataclass
class DemoTransaction:
    id: int
    value: int


@dataclass
class DemoBlock:
    index: int
    previous: int
    transactions: List[DemoTransaction] = field(default_factory=list)
    r: int = field(default_factory=lambda: random.randint(1, q))
    id: int = 0

    def compute_id(self) -> int:
        m = msg_for_block([t.id for t in self.transactions], self.previous)
        return chameleonHash(PK, m, self.r)

    def seal(self) -> None:
        self.id = self.compute_id()

    def redact_modify_tx(self, tx_index: int, new_value: int, trapdoor_sk: int) -> None:
        """Modify a tx value and adjust r so the block id stays unchanged."""
        if not (0 <= tx_index < len(self.transactions)):
            raise IndexError("tx_index out of range")

        # m1 and old r
        m1 = msg_for_block([t.id for t in self.transactions], self.previous)
        r1 = self.r
        id_before = self.compute_id()

        # mutate transaction (simulate redact/modify)
        self.transactions[tx_index].value = new_value

        # m2 and forged r2 to keep CH(m2, r2) == CH(m1, r1)
        m2 = msg_for_block([t.id for t in self.transactions], self.previous)
        r2 = forge(trapdoor_sk, m1, r1, m2)
        self.r = r2
        self.id = self.compute_id()

        assert self.id == id_before, "Chameleon collision failed: id changed after redaction"

    def redact_delete_tx(self, tx_index: int, trapdoor_sk: int) -> None:
        """Delete a tx and adjust r so the block id stays unchanged."""
        if not (0 <= tx_index < len(self.transactions)):
            raise IndexError("tx_index out of range")

        m1 = msg_for_block([t.id for t in self.transactions], self.previous)
        r1 = self.r
        id_before = self.compute_id()

        # delete the transaction
        self.transactions.pop(tx_index)

        m2 = msg_for_block([t.id for t in self.transactions], self.previous)
        r2 = forge(trapdoor_sk, m1, r1, m2)
        self.r = r2
        self.id = self.compute_id()

        assert self.id == id_before, "Chameleon collision failed: id changed after deletion"


def verify_chain(blocks: List[DemoBlock]) -> bool:
    """Verify chain linkage and block ids match their contents via CH."""
    for i, b in enumerate(blocks):
        # verify id matches contents
        if b.compute_id() != b.id:
            return False
        # verify previous pointers
        if i > 0 and b.previous != blocks[i - 1].id:
            return False
    return True


def build_demo_chain() -> List[DemoBlock]:
    """Build a tiny chain of 3 blocks with a few transactions each."""
    # genesis
    genesis = DemoBlock(index=0, previous=0, transactions=[DemoTransaction(id=1, value=50)])
    genesis.seal()

    # block 1
    b1 = DemoBlock(
        index=1,
        previous=genesis.id,
        transactions=[
            DemoTransaction(id=2, value=25),
            DemoTransaction(id=3, value=75),
            DemoTransaction(id=4, value=10),
        ],
    )
    b1.seal()

    # block 2
    b2 = DemoBlock(
        index=2,
        previous=b1.id,
        transactions=[
            DemoTransaction(id=5, value=5),
            DemoTransaction(id=6, value=15),
        ],
    )
    b2.seal()

    return [genesis, b1, b2]


def print_chain(blocks: List[DemoBlock], title: str) -> None:
    print(f"\n{title}")
    print("=" * len(title))
    for b in blocks:
        print(f"Block {b.index}: id={b.id} prev={b.previous} r={b.r}")
        print(f"  txs: {[t.id for t in b.transactions]}")


def run_demo():
    print("Redactable Blockchain – Chameleon Hash Redaction Demo")
    print("-" * 60)

    # Note: We use the globally configured trapdoor SK through forge().
    # The CH module exposes PK and the trapdoor-based forge operation.
    from CH.ChameleonHash import SK  # import here to keep top clean

    chain = build_demo_chain()
    assert verify_chain(chain)
    print_chain(chain, "Original chain")

    # Perform a MODIFY redaction on block 1, tx index 1
    target_block = chain[1]
    print("\nRedacting block 1: MODIFY tx[1] value -> 999 (Ateniese-style)")
    before_id = target_block.id
    target_block.redact_modify_tx(tx_index=1, new_value=999, trapdoor_sk=SK)
    after_id = target_block.id
    print(f"  id before = {before_id}")
    print(f"  id after  = {after_id}")
    print("  Redaction preserved block id via forged r")

    # Child block still links to the same id
    chain[2].previous = chain[1].id  # unchanged logically
    assert verify_chain(chain)
    print_chain(chain, "Chain after MODIFY redaction (ids unchanged)")

    # Perform a DELETE redaction on block 1, remove tx index 0
    print("\nRedacting block 1: DELETE tx[0]")
    before_id_del = chain[1].id
    chain[1].redact_delete_tx(tx_index=0, trapdoor_sk=SK)
    after_id_del = chain[1].id
    print(f"  id before = {before_id_del}")
    print(f"  id after  = {after_id_del}")
    print("  Redaction preserved block id via forged r")

    assert verify_chain(chain)
    print_chain(chain, "Final chain after DELETE redaction (ids unchanged)")

    print("\nDemo complete: contents changed, chain remained valid (ids stable).")


if __name__ == "__main__":
    run_demo()
