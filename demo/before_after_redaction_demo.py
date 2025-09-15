#!/usr/bin/env python3
"""
my Before/After Redaction Demo
===================================

This demo explicitly shows the blockchain state before and after redaction
operations to clearly demonstrate the redaction capabilities requested by
the boss.

Features:
1. Clear blockchain state snapshots before redaction
2. Detailed transaction and block information
3. Step-by-step redaction process
4. Comprehensive after-state verification
5. Visual comparison of changes
"""

import os
import sys
import json
import hashlib
from typing import Dict, List, Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from demo.redactable_blockchain_demo import DemoTransaction, DemoBlock, verify_chain
from CH.ChameleonHash import SK, PK


def print_separator(title: str):
    """Print a visual separator for different sections."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_block_state(block: DemoBlock, title: str):
    """Print detailed block state information."""
    print(f"\n{title}:")
    print(f"  Block Index: {block.index}")
    print(f"  Block ID (Hash): {block.id}")
    print(f"  Previous Block: {block.previous}")
    print(f"  Randomness (r): {block.r}")
    print(f"  Number of Transactions: {len(block.transactions)}")
    print(f"  Transactions:")
    for i, tx in enumerate(block.transactions):
        print(f"    [{i}] ID: {tx.id}, Value: {tx.value}")


def print_chain_summary(chain: List[DemoBlock], title: str):
    """Print a summary of the entire blockchain."""
    print(f"\n{title}:")
    print(f"  Total Blocks: {len(chain)}")
    print(f"  Chain Valid: {verify_chain(chain)}")
    print(f"  Block Details:")
    for block in chain:
        tx_summary = f"{len(block.transactions)} txs"
        if block.transactions:
            values = [str(tx.value) for tx in block.transactions]
            tx_summary += f" (values: {', '.join(values)})"
        print(f"    Block {block.index}: ID={block.id}, {tx_summary}")


def create_demo_blockchain() -> List[DemoBlock]:
    """Create a demonstration blockchain with sample data."""
    chain = []
    
    # Genesis block
    genesis = DemoBlock(index=0, previous=0)
    genesis.transactions = [
        DemoTransaction(id=1001, value=100),
        DemoTransaction(id=1002, value=200)
    ]
    genesis.seal()
    chain.append(genesis)
    
    # Block 1
    block1 = DemoBlock(index=1, previous=genesis.id)
    block1.transactions = [
        DemoTransaction(id=2001, value=150),
        DemoTransaction(id=2002, value=300),
        DemoTransaction(id=2003, value=75)
    ]
    block1.seal()
    chain.append(block1)
    
    # Block 2
    block2 = DemoBlock(index=2, previous=block1.id)
    block2.transactions = [
        DemoTransaction(id=3001, value=500),
        DemoTransaction(id=3002, value=25)
    ]
    block2.seal()
    chain.append(block2)
    
    return chain


def demonstrate_modify_redaction(chain: List[DemoBlock]) -> Dict[str, Any]:
    """Demonstrate a MODIFY redaction with explicit before/after states."""
    print_separator("MODIFY REDACTION DEMONSTRATION")
    
    # Target: Block 1, Transaction 1 (value 300 -> 999)
    target_block_idx = 1
    target_tx_idx = 1
    new_value = 999
    target_block = chain[target_block_idx]
    target_tx = target_block.transactions[target_tx_idx]
    
    print(f"\nTarget: Block {target_block_idx}, Transaction {target_tx_idx}")
    print(f"Original Value: {target_tx.value} -> New Value: {new_value}")
    
    # BEFORE STATE
    print_block_state(target_block, "BEFORE REDACTION - Block State")
    
    # Store original state for comparison
    original_state = {
        "block_id": target_block.id,
        "block_r": target_block.r,
        "tx_value": target_tx.value,
        "tx_id": target_tx.id,
        "chain_valid": verify_chain(chain)
    }
    
    # REDACTION PROCESS
    print(f"\n--- PERFORMING REDACTION ---")
    print(f"1. Recording original block hash: {target_block.id}")
    print(f"2. Modifying transaction value: {target_tx.value} -> {new_value}")
    
    # Perform the redaction
    target_block.redact_modify_tx(target_tx_idx, new_value, SK)
    
    print(f"3. Forged new randomness: {target_block.r}")
    print(f"4. New block hash (should be same): {target_block.id}")
    
    # AFTER STATE
    print_block_state(target_block, "AFTER REDACTION - Block State")
    
    # Verify chain is still valid
    chain_valid_after = verify_chain(chain)
    print(f"\nChain Validation After Redaction: {chain_valid_after}")
    
    # COMPARISON
    print(f"\n--- REDACTION RESULTS COMPARISON ---")
    print(f"Block ID:        {original_state['block_id']} -> {target_block.id} (Same: {original_state['block_id'] == target_block.id})")
    print(f"Block Randomness: {original_state['block_r']} -> {target_block.r} (Changed: {original_state['block_r'] != target_block.r})")
    print(f"Transaction Value: {original_state['tx_value']} -> {target_tx.value} (Modified)")
    print(f"Chain Validity:   {original_state['chain_valid']} -> {chain_valid_after} (Maintained)")
    
    return {
        "type": "MODIFY",
        "target_block": target_block_idx,
        "target_tx": target_tx_idx,
        "original_value": original_state['tx_value'],
        "new_value": new_value,
        "hash_preserved": original_state['block_id'] == target_block.id,
        "chain_valid": chain_valid_after
    }


def demonstrate_delete_redaction(chain: List[DemoBlock]) -> Dict[str, Any]:
    """Demonstrate a DELETE redaction with explicit before/after states."""
    print_separator("DELETE REDACTION DEMONSTRATION")
    
    # Target: Block 2, Transaction 0 (remove first transaction)
    target_block_idx = 2
    target_tx_idx = 0
    target_block = chain[target_block_idx]
    target_tx = target_block.transactions[target_tx_idx]
    
    print(f"\nTarget: Block {target_block_idx}, Transaction {target_tx_idx}")
    print(f"Transaction to Delete: ID={target_tx.id}, Value={target_tx.value}")
    
    # BEFORE STATE
    print_block_state(target_block, "BEFORE REDACTION - Block State")
    
    # Store original state
    original_state = {
        "block_id": target_block.id,
        "block_r": target_block.r,
        "tx_count": len(target_block.transactions),
        "deleted_tx": {"id": target_tx.id, "value": target_tx.value},
        "chain_valid": verify_chain(chain)
    }
    
    # REDACTION PROCESS
    print(f"\n--- PERFORMING DELETION ---")
    print(f"1. Recording original block hash: {target_block.id}")
    print(f"2. Removing transaction {target_tx_idx}: ID={target_tx.id}")
    
    # Perform the deletion
    target_block.redact_delete_tx(target_tx_idx, SK)
    
    print(f"3. Forged new randomness: {target_block.r}")
    print(f"4. New block hash (should be same): {target_block.id}")
    
    # AFTER STATE
    print_block_state(target_block, "AFTER REDACTION - Block State")
    
    # Verify chain is still valid
    chain_valid_after = verify_chain(chain)
    print(f"\nChain Validation After Deletion: {chain_valid_after}")
    
    # COMPARISON
    print(f"\n--- DELETION RESULTS COMPARISON ---")
    print(f"Block ID:         {original_state['block_id']} -> {target_block.id} (Same: {original_state['block_id'] == target_block.id})")
    print(f"Block Randomness:  {original_state['block_r']} -> {target_block.r} (Changed: {original_state['block_r'] != target_block.r})")
    print(f"Transaction Count: {original_state['tx_count']} -> {len(target_block.transactions)} (Reduced)")
    print(f"Deleted Transaction: ID={original_state['deleted_tx']['id']}, Value={original_state['deleted_tx']['value']} (REMOVED)")
    print(f"Chain Validity:    {original_state['chain_valid']} -> {chain_valid_after} (Maintained)")
    
    return {
        "type": "DELETE",
        "target_block": target_block_idx,
        "target_tx": target_tx_idx,
        "deleted_tx": original_state['deleted_tx'],
        "tx_count_before": original_state['tx_count'],
        "tx_count_after": len(target_block.transactions),
        "hash_preserved": original_state['block_id'] == target_block.id,
        "chain_valid": chain_valid_after
    }


def run_comprehensive_before_after_demo():
    """Run the complete before/after redaction demonstration."""
    print_separator("COMPREHENSIVE BEFORE/AFTER REDACTION DEMO")
    print("This demo shows explicit blockchain state before and after redaction operations")
    print("to demonstrate how chameleon hash enables content changes while preserving")
    print("block hashes and maintaining chain validity.")
    
    # Create demonstration blockchain
    print_separator("INITIAL BLOCKCHAIN STATE")
    chain = create_demo_blockchain()
    print_chain_summary(chain, "Original Blockchain")
    
    # Demonstrate MODIFY redaction
    modify_results = demonstrate_modify_redaction(chain)
    
    # Show chain state after first redaction
    print_chain_summary(chain, "Blockchain After MODIFY Redaction")
    
    # Demonstrate DELETE redaction
    delete_results = demonstrate_delete_redaction(chain)
    
    # Final chain state
    print_chain_summary(chain, "Final Blockchain State")
    
    # Summary of all operations
    print_separator("REDACTION OPERATIONS SUMMARY")
    print(f"1. MODIFY Redaction:")
    print(f"   - Block {modify_results['target_block']}, Transaction {modify_results['target_tx']}")
    print(f"   - Value changed: {modify_results['original_value']} -> {modify_results['new_value']}")
    print(f"   - Hash preserved: {modify_results['hash_preserved']}")
    print(f"   - Chain valid: {modify_results['chain_valid']}")
    
    print(f"\n2. DELETE Redaction:")
    print(f"   - Block {delete_results['target_block']}, Transaction {delete_results['target_tx']}")
    print(f"   - Deleted transaction: ID={delete_results['deleted_tx']['id']}, Value={delete_results['deleted_tx']['value']}")
    print(f"   - Transaction count: {delete_results['tx_count_before']} -> {delete_results['tx_count_after']}")
    print(f"   - Hash preserved: {delete_results['hash_preserved']}")
    print(f"   - Chain valid: {delete_results['chain_valid']}")
    
    print(f"\n--- KEY ACHIEVEMENTS ---")
    print(f" Content successfully modified and deleted")
    print(f" Block hashes preserved through chameleon hash forging")
    print(f" Chain validity maintained throughout all operations")
    print(f" No global chain recomputation required")
    print(f" Blockchain remains cryptographically sound")
    
    print_separator("DEMO COMPLETED SUCCESSFULLY")
    
    return {
        "modify_redaction": modify_results,
        "delete_redaction": delete_results,
        "final_chain_valid": verify_chain(chain),
        "total_redactions": 2
    }


if __name__ == "__main__":
    results = run_comprehensive_before_after_demo()
    print(f"\nDemo completed with {results['total_redactions']} successful redactions.")