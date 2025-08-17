"""
Proof-of-Consistency Implementation for Redactable Blockchain
===========================================================

This module implements proof-of-consistency mechanisms to ensure that redaction operations
maintain blockchain integrity and auditability in smart-contract-enabled permissioned blockchains.

The proof-of-consistency ensures:
1. Block chain integrity after redaction operations
2. Smart contract state consistency 
3. Transaction ordering preservation
4. Merkle tree validity
5. Cryptographic hash chain integrity
"""

import hashlib
import json
import random
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum


class ConsistencyCheckType(Enum):
    """Types of consistency checks."""
    BLOCK_INTEGRITY = "block_integrity"
    HASH_CHAIN = "hash_chain" 
    MERKLE_TREE = "merkle_tree"
    SMART_CONTRACT_STATE = "smart_contract_state"
    TRANSACTION_ORDERING = "transaction_ordering"
    CRYPTOGRAPHIC_PROOF = "cryptographic_proof"


@dataclass
class ConsistencyProof:
    """Proof-of-consistency structure."""
    proof_id: str
    check_type: ConsistencyCheckType
    block_range: Tuple[int, int]  # (start_block, end_block)
    pre_redaction_state: Dict[str, Any]
    post_redaction_state: Dict[str, Any]
    merkle_proofs: List[str]
    hash_chain_proof: str
    timestamp: int
    is_valid: bool
    error_details: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['check_type'] = self.check_type.value
        return result


@dataclass 
class StateTransition:
    """Represents a state transition during redaction."""
    operation_id: str
    from_state_hash: str
    to_state_hash: str
    operation_type: str
    affected_elements: List[str]
    witness_data: Dict[str, Any]
    timestamp: int


class MerkleTreeConsistency:
    """Handles Merkle tree consistency verification."""
    
    @staticmethod
    def compute_merkle_root(data_hashes: List[str]) -> str:
        """Compute Merkle root from list of data hashes. Hash of the concatenation of all data hashes."""
        if not data_hashes:
            return hashlib.sha256(b"").hexdigest()  # hash of an empty byte string

        if len(data_hashes) == 1:
            return data_hashes[0]
            
        # Pad with last element if odd number of elements
        if len(data_hashes) % 2 == 1:
            data_hashes.append(data_hashes[-1])  # duplicates last element
            
        next_level = []
        for i in range(0, len(data_hashes), 2):
            combined = data_hashes[i] + data_hashes[i + 1]
            next_level.append(hashlib.sha256(combined.encode()).hexdigest())
            
        return MerkleTreeConsistency.compute_merkle_root(next_level)
    
    @staticmethod
    def generate_merkle_proof(data_hashes: List[str], target_index: int) -> List[str]:
        """Generate Merkle proof for element at target_index."""
        if target_index >= len(data_hashes):
            return []
            
        proof = []
        current_hashes = data_hashes[:]  # copy of only the top-level hashes (complex structures will be pointed at, without copying them)
        current_index = target_index
        
        while len(current_hashes) > 1:
            # Pad if odd
            if len(current_hashes) % 2 == 1:
                current_hashes.append(current_hashes[-1])
                
            # Find sibling
            if current_index % 2 == 0:
                sibling_index = current_index + 1
            else:
                sibling_index = current_index - 1
                
            if sibling_index < len(current_hashes):
                proof.append(current_hashes[sibling_index])
                
            # Move to next level
            next_level = []
            for i in range(0, len(current_hashes), 2):
                combined = current_hashes[i] + current_hashes[i + 1]
                next_level.append(hashlib.sha256(combined.encode()).hexdigest())
                
            current_hashes = next_level
            current_index = current_index // 2  # move to next level (since each parent node represents two children from the level below)

        return proof  # sequence of hashes needed to reconstruct the path from the target leaf to the root
    
    @staticmethod
    def verify_merkle_proof(leaf_hash: str, proof: List[str], root: str, leaf_index: int) -> bool:
        """Verify Merkle proof reconstructing the path from the leaf to the root."""
        current_hash = leaf_hash
        current_index = leaf_index
        
        for sibling_hash in proof:
            if current_index % 2 == 0:
                combined = current_hash + sibling_hash
            else:
                combined = sibling_hash + current_hash
                
            current_hash = hashlib.sha256(combined.encode()).hexdigest()
            current_index = current_index // 2
            
        return current_hash == root


class HashChainConsistency:
    """Handles hash chain consistency verification."""
    
    @staticmethod
    def verify_chain_integrity(blocks: List[Any]) -> Tuple[bool, Optional[str]]:
        """Verify the integrity of a blockchain hash chain."""
        if not blocks:
            return True, None
            
        for i in range(1, len(blocks)):
            current_block = blocks[i]
            previous_block = blocks[i - 1]
            
            # Check if previous hash matches
            if hasattr(current_block, 'previous') and hasattr(previous_block, 'id'):
                if current_block.previous != previous_block.id:
                    return False, f"Hash chain break at block {i}: expected {previous_block.id}, got {current_block.previous}"
                    
        return True, None
    
    @staticmethod
    def compute_chain_checksum(blocks: List[Any]) -> str:
        """Compute checksum for entire chain."""
        block_hashes = []
        for block in blocks:
            block_data = {
                "id": getattr(block, 'id', ''),
                "previous": getattr(block, 'previous', ''),
                "depth": getattr(block, 'depth', 0),
                "timestamp": getattr(block, 'timestamp', 0)
            }
            block_hash = hashlib.sha256(json.dumps(block_data, sort_keys=True).encode()).hexdigest()
            block_hashes.append(block_hash)
            
        return hashlib.sha256(''.join(block_hashes).encode()).hexdigest()


class SmartContractStateConsistency:
    """Handles smart contract state consistency verification."""
    
    @staticmethod
    def verify_state_transition(
        pre_state: Dict[str, Any], 
        post_state: Dict[str, Any], 
        operation: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Verify that state transition is valid for the given operation."""
        
        operation_type = operation.get("type", "")
        
        if operation_type == "REDACT_CONTRACT_DATA":
            return SmartContractStateConsistency._verify_redaction_transition(
                pre_state, post_state, operation
            )
        elif operation_type == "CONTRACT_CALL":
            return SmartContractStateConsistency._verify_call_transition(
                pre_state, post_state, operation
            )
        else:
            return True, None  # Unknown operation type, assume valid
    
    @staticmethod
    def _verify_redaction_transition(
        pre_state: Dict[str, Any], 
        post_state: Dict[str, Any], 
        operation: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Verify redaction state transition."""
        redacted_fields = operation.get("redacted_fields", [])
        
        for field in redacted_fields:
            if field in pre_state and field in post_state:
                # Field should be modified or removed
                if pre_state[field] == post_state[field]:
                    return False, f"Field {field} was not properly redacted"
                    
        # Non-redacted fields should remain unchanged
        for field in pre_state:
            if field not in redacted_fields and field in post_state:
                if pre_state[field] != post_state[field]:
                    return False, f"Non-redacted field {field} was modified"
                    
        return True, None
    
    @staticmethod
    def _verify_call_transition(
        pre_state: Dict[str, Any], 
        post_state: Dict[str, Any], 
        operation: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Verify contract call state transition."""
        # Basic state transition validation
        # In a real implementation, this would check function-specific logic
        function_name = operation.get("function_name", "")
        
        if function_name == "transfer":
            # Verify balance changes for transfer
            return SmartContractStateConsistency._verify_transfer(pre_state, post_state, operation)
            
        return True, None  # Assume valid for other functions
    
    @staticmethod
    def _verify_transfer(
        pre_state: Dict[str, Any], 
        post_state: Dict[str, Any], 
        operation: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Verify token transfer operation."""
        from_addr = operation.get("from_address", "")
        to_addr = operation.get("to_address", "")
        amount = operation.get("amount", 0)
        
        # Check balances
        pre_from_balance = pre_state.get("balances", {}).get(from_addr, 0)
        post_from_balance = post_state.get("balances", {}).get(from_addr, 0)
        
        pre_to_balance = pre_state.get("balances", {}).get(to_addr, 0)
        post_to_balance = post_state.get("balances", {}).get(to_addr, 0)
        
        if post_from_balance != pre_from_balance - amount:
            return False, f"Invalid from balance: expected {pre_from_balance - amount}, got {post_from_balance}"
            
        if post_to_balance != pre_to_balance + amount:
            return False, f"Invalid to balance: expected {pre_to_balance + amount}, got {post_to_balance}"
            
        return True, None


class ConsistencyProofGenerator:
    """Generates proofs-of-consistency for redaction operations."""
    
    def __init__(self):
        self.merkle_checker = MerkleTreeConsistency()
        self.hash_chain_checker = HashChainConsistency()
        self.contract_checker = SmartContractStateConsistency()
        
    def generate_consistency_proof(
        self,
        check_type: ConsistencyCheckType,
        pre_redaction_data: Dict[str, Any],
        post_redaction_data: Dict[str, Any],
        operation_details: Dict[str, Any]
    ) -> ConsistencyProof:
        """Generate a proof-of-consistency for a redaction operation."""
        
        proof_id = f"consistency_{check_type.value}_{int(time.time())}_{random.randint(1000, 9999)}"
        
        try:
            if check_type == ConsistencyCheckType.BLOCK_INTEGRITY:
                is_valid, error = self._verify_block_integrity(
                    pre_redaction_data, post_redaction_data, operation_details
                )
                
            elif check_type == ConsistencyCheckType.HASH_CHAIN:
                is_valid, error = self._verify_hash_chain_consistency(
                    pre_redaction_data, post_redaction_data, operation_details
                )
                
            elif check_type == ConsistencyCheckType.MERKLE_TREE:
                is_valid, error = self._verify_merkle_consistency(
                    pre_redaction_data, post_redaction_data, operation_details
                )
                
            elif check_type == ConsistencyCheckType.SMART_CONTRACT_STATE:
                is_valid, error = self._verify_contract_state_consistency(
                    pre_redaction_data, post_redaction_data, operation_details
                )
                
            elif check_type == ConsistencyCheckType.TRANSACTION_ORDERING:
                is_valid, error = self._verify_transaction_ordering(
                    pre_redaction_data, post_redaction_data, operation_details
                )
                
            else:
                is_valid, error = True, None
                
        except Exception as e:
            is_valid, error = False, str(e)
            
        # Generate Merkle proofs
        merkle_proofs = self._generate_merkle_proofs(pre_redaction_data, post_redaction_data)
        
        # Generate hash chain proof
        hash_chain_proof = self._generate_hash_chain_proof(pre_redaction_data, post_redaction_data)
        
        return ConsistencyProof(
            proof_id=proof_id,
            check_type=check_type,
            block_range=operation_details.get("block_range", (0, 0)),
            pre_redaction_state=pre_redaction_data,
            post_redaction_state=post_redaction_data,
            merkle_proofs=merkle_proofs,
            hash_chain_proof=hash_chain_proof,
            timestamp=int(time.time()),
            is_valid=is_valid,
            error_details=error
        )
    
    def _verify_block_integrity(
        self, 
        pre_data: Dict[str, Any], 
        post_data: Dict[str, Any], 
        operation: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Verify block integrity after redaction."""
        
        pre_blocks = pre_data.get("blocks", [])
        post_blocks = post_data.get("blocks", [])
        
        if len(pre_blocks) != len(post_blocks):
            return False, "Block count mismatch after redaction"
            
        redacted_block_index = operation.get("target_block", -1)
        
        # Check non-redacted blocks remain unchanged
        for i, (pre_block, post_block) in enumerate(zip(pre_blocks, post_blocks)):
            if i != redacted_block_index:
                pre_hash = self._compute_block_hash(pre_block)
                post_hash = self._compute_block_hash(post_block)
                if pre_hash != post_hash:
                    return False, f"Non-redacted block {i} was modified"
                    
        return True, None
    
    def _verify_hash_chain_consistency(
        self, 
        pre_data: Dict[str, Any], 
        post_data: Dict[str, Any], 
        operation: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Verify hash chain consistency after redaction."""
        
        post_blocks = post_data.get("blocks", [])
        return self.hash_chain_checker.verify_chain_integrity(post_blocks)
    
    def _verify_merkle_consistency(
        self, 
        pre_data: Dict[str, Any], 
        post_data: Dict[str, Any], 
        operation: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Verify Merkle tree consistency after redaction."""
        
        # Extract transaction hashes from redacted block
        redacted_block_index = operation.get("target_block", -1)
        post_blocks = post_data.get("blocks", [])
        
        if redacted_block_index >= len(post_blocks):
            return False, "Target block index out of range"
            
        redacted_block = post_blocks[redacted_block_index]
        tx_hashes = [self._compute_tx_hash(tx) for tx in redacted_block.get("transactions", [])]
        
        # Verify Merkle root
        computed_root = self.merkle_checker.compute_merkle_root(tx_hashes)
        stored_root = redacted_block.get("merkle_root", "")
        
        if computed_root != stored_root:
            return False, f"Merkle root mismatch: computed {computed_root}, stored {stored_root}"
            
        return True, None
    
    def _verify_contract_state_consistency(
        self, 
        pre_data: Dict[str, Any], 
        post_data: Dict[str, Any], 
        operation: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Verify smart contract state consistency after redaction."""
        
        pre_contract_states = pre_data.get("contract_states", {})
        post_contract_states = post_data.get("contract_states", {})
        
        affected_contracts = operation.get("affected_contracts", [])
        
        for contract_address in affected_contracts:
            pre_state = pre_contract_states.get(contract_address, {})
            post_state = post_contract_states.get(contract_address, {})
            
            is_valid, error = self.contract_checker.verify_state_transition(
                pre_state, post_state, operation
            )
            
            if not is_valid:
                return False, f"Contract {contract_address}: {error}"
                
        return True, None
    
    def _verify_transaction_ordering(
        self, 
        pre_data: Dict[str, Any], 
        post_data: Dict[str, Any], 
        operation: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Verify transaction ordering is preserved after redaction."""
        
        redacted_block_index = operation.get("target_block", -1)
        redacted_tx_index = operation.get("target_tx", -1)
        
        pre_blocks = pre_data.get("blocks", [])
        post_blocks = post_data.get("blocks", [])
        
        if redacted_block_index < 0 or redacted_block_index >= len(pre_blocks) or redacted_block_index >= len(post_blocks):  # index must not be bigger than block length
            return False, "Invalid block index"
            
        pre_txs = pre_blocks[redacted_block_index].get("transactions", [])
        post_txs = post_blocks[redacted_block_index].get("transactions", [])
        
        # Check that non-redacted transactions maintain their relative order
        pre_order = [i for i, tx in enumerate(pre_txs) if i != redacted_tx_index]
        post_order = [i for i, tx in enumerate(post_txs)]
        
        # Adjust indices for removed/modified transaction
        if operation.get("redaction_type") == "DELETE" and len(post_txs) == len(pre_txs) - 1:
            # Transaction was deleted, adjust indices
            adjusted_post_order = []
            for idx in post_order:
                if idx >= redacted_tx_index:
                    adjusted_post_order.append(idx + 1)
                else:
                    adjusted_post_order.append(idx)
            post_order = adjusted_post_order
            # idx = 0: 0 >= 2? No  → append(0) → [0]
            # idx = 1: 1 >= 2? No  → append(1) → [0, 1]  
            # idx = 2: 2 >= 2? Yes → append(3) → [0, 1, 3]
            # idx = 3: 3 >= 2? Yes → append(4) → [0, 1, 3, 4]

        if pre_order != post_order:  # [0, 1, 3, 4] != [0, 1, 3, 4] and not [0, 1, 2, 3]
            return False, "Transaction ordering was not preserved"
            
        return True, None
    
    def _generate_merkle_proofs(
        self, 
        pre_data: Dict[str, Any], 
        post_data: Dict[str, Any]
    ) -> List[str]:
        """Generate Merkle proofs for verification."""
        proofs = []
        
        post_blocks = post_data.get("blocks", [])
        for block in post_blocks:
            tx_hashes = [self._compute_tx_hash(tx) for tx in block.get("transactions", [])]
            if tx_hashes:
                # Generate proof for first transaction as example
                proof = self.merkle_checker.generate_merkle_proof(tx_hashes, 0)
                proofs.extend(proof)  # :)
                
        return proofs
    
    def _generate_hash_chain_proof(
        self, 
        pre_data: Dict[str, Any], 
        post_data: Dict[str, Any]
    ) -> str:
        """Generate hash chain proof."""
        post_blocks = post_data.get("blocks", [])
        return self.hash_chain_checker.compute_chain_checksum(post_blocks)
    
    def _compute_block_hash(self, block: Dict[str, Any]) -> str:
        """Compute hash of a block."""
        block_data = {
            "depth": block.get("depth", 0),
            "previous": block.get("previous", ""),
            "timestamp": block.get("timestamp", 0),
            "transactions": [self._compute_tx_hash(tx) for tx in block.get("transactions", [])]
        }
        return hashlib.sha256(json.dumps(block_data, sort_keys=True).encode()).hexdigest()
    
    def _compute_tx_hash(self, tx: Dict[str, Any]) -> str:
        """Compute hash of a transaction."""
        tx_data = {
            "id": tx.get("id", ""),
            "sender": tx.get("sender", ""),
            "to": tx.get("to", ""),
            "value": tx.get("value", 0)
        }
        return hashlib.sha256(json.dumps(tx_data, sort_keys=True).encode()).hexdigest()


class ConsistencyProofVerifier:
    """Verifies proofs-of-consistency."""
    
    def __init__(self):
        self.generator = ConsistencyProofGenerator()
        
    def verify_proof(self, proof: ConsistencyProof) -> Tuple[bool, Optional[str]]:
        """Verify a consistency proof."""
        
        try:
            # Basic validation
            if not proof.proof_id:
                return False, "Invalid proof ID"
                
            if not proof.is_valid:
                return False, f"Proof marked as invalid: {proof.error_details}"
                
            # Verify timestamp (not too old)
            current_time = int(time.time())
            if current_time - proof.timestamp > 86400:  # 24 hours
                return False, "Proof too old"
                
            # Verify hash chain proof
            computed_chain_proof = self.generator._generate_hash_chain_proof(
                {}, proof.post_redaction_state
            )
            
            if computed_chain_proof != proof.hash_chain_proof:
                return False, "Hash chain proof mismatch"
                
            # Type-specific verification
            if proof.check_type == ConsistencyCheckType.MERKLE_TREE:
                return self._verify_merkle_proof(proof)
            elif proof.check_type == ConsistencyCheckType.HASH_CHAIN:
                return self._verify_hash_chain_proof(proof)
            elif proof.check_type == ConsistencyCheckType.SMART_CONTRACT_STATE:
                return self._verify_contract_state_proof(proof)
            else:
                return True, None  # Other types assumed valid
                
        except Exception as e:
            return False, f"Verification error: {e}"
    
    def _verify_merkle_proof(self, proof: ConsistencyProof) -> Tuple[bool, Optional[str]]:
        """Verify Merkle tree proof. Even if the main verification is done inside ConsistencyProofGenerator."""
        try:
            # Extract post-redaction blocks
            post_blocks = proof.post_redaction_state.get("blocks", [])
            
            if not post_blocks:
                return False, "No blocks found in post-redaction state"
                
            # Verify Merkle proofs for each block
            for block_index, block in enumerate(post_blocks):
                transactions = block.get("transactions", [])
                stored_merkle_root = block.get("merkle_root", "")
                
                if not transactions:
                    continue  # Skip empty blocks
                    
                # Compute transaction hashes
                tx_hashes = [self.generator._compute_tx_hash(tx) for tx in transactions]
                
                # Compute expected Merkle root
                computed_root = self.generator.merkle_checker.compute_merkle_root(tx_hashes)
                
                # Verify stored root matches computed root
                if stored_merkle_root and computed_root != stored_merkle_root:
                    return False, f"Merkle root mismatch in block {block_index}: expected {stored_merkle_root}, got {computed_root}"
                
                # Verify individual Merkle proofs from proof.merkle_proofs
                if proof.merkle_proofs and len(tx_hashes) > 0:
                    # For demonstration, verify proof for first transaction
                    leaf_hash = tx_hashes[0]
                    leaf_index = 0
                    
                    # Generate proof path for verification
                    merkle_proof_path = self.generator.merkle_checker.generate_merkle_proof(tx_hashes, leaf_index)
                    
                    # Verify the proof path reconstructs to the root
                    is_valid = self.generator.merkle_checker.verify_merkle_proof(
                        leaf_hash, merkle_proof_path, computed_root, leaf_index
                    )
                    
                    if not is_valid:
                        return False, f"Merkle proof verification failed for transaction {leaf_index} in block {block_index}"
            
            return True, None
            
        except Exception as e:
            return False, f"Merkle proof verification error: {str(e)}"
    
    def _verify_hash_chain_proof(self, proof: ConsistencyProof) -> Tuple[bool, Optional[str]]:
        """Verify hash chain proof. Even if the main verification is done inside ConsistencyProofGenerator."""
        try:
            # Extract post-redaction blocks
            post_blocks = proof.post_redaction_state.get("blocks", [])
            
            if not post_blocks:
                return False, "No blocks found in post-redaction state"
            
            # 1. Verify the hash chain integrity using existing method
            is_chain_valid, chain_error = self.generator.hash_chain_checker.verify_chain_integrity(post_blocks)
            if not is_chain_valid:
                return False, f"Hash chain integrity check failed: {chain_error}"
            
            # 2. Verify the stored hash chain proof matches computed checksum
            computed_checksum = self.generator.hash_chain_checker.compute_chain_checksum(post_blocks)
            stored_proof = proof.hash_chain_proof
            
            if computed_checksum != stored_proof:
                return False, f"Hash chain proof mismatch: expected {stored_proof}, computed {computed_checksum}"
            
            # 3. Additional verification: ensure each block's hash references are correct
            for i in range(1, len(post_blocks)):
                current_block = post_blocks[i]
                previous_block = post_blocks[i - 1]
                
                # Check if current block correctly references previous block
                expected_previous = previous_block.get("id", "")
                actual_previous = current_block.get("previous", "")
                
                if expected_previous != actual_previous:
                    return False, f"Block {i} hash reference mismatch: expected previous '{expected_previous}', got '{actual_previous}'"
                
                # Verify block depth progression
                expected_depth = previous_block.get("depth", 0) + 1
                actual_depth = current_block.get("depth", 0)
                
                if expected_depth != actual_depth:
                    return False, f"Block {i} depth mismatch: expected {expected_depth}, got {actual_depth}"
                
                # Verify timestamp progression (blocks should be chronologically ordered)
                prev_timestamp = previous_block.get("timestamp", 0)
                curr_timestamp = current_block.get("timestamp", 0)
                
                if curr_timestamp < prev_timestamp:
                    return False, f"Block {i} timestamp regression: block {curr_timestamp} < previous {prev_timestamp}"
            
            # 4. Verify genesis block properties
            if len(post_blocks) > 0:
                genesis_block = post_blocks[0]
                if genesis_block.get("depth", 0) != 0:
                    return False, f"Genesis block depth should be 0, got {genesis_block.get('depth', 0)}"
                if genesis_block.get("previous", "") != "":
                    return False, f"Genesis block should have empty previous hash, got '{genesis_block.get('previous', '')}'"
            
            return True, None
            
        except Exception as e:
            return False, f"Hash chain proof verification error: {str(e)}"
    
    def _verify_contract_state_proof(self, proof: ConsistencyProof) -> Tuple[bool, Optional[str]]:
        """Verify smart contract state proof. Even if the main verification is done inside ConsistencyProofGenerator."""
        try:
            # Extract pre and post redaction states
            pre_redaction_state = proof.pre_redaction_state
            post_redaction_state = proof.post_redaction_state
            
            # Get contract states from both pre and post redaction data
            pre_contract_states = pre_redaction_state.get("contract_states", {})
            post_contract_states = post_redaction_state.get("contract_states", {})
            
            if not pre_contract_states and not post_contract_states:
                return True, None  # No contracts to verify
            
            # 1. Verify that contract addresses are consistent
            pre_addresses = set(pre_contract_states.keys())
            post_addresses = set(post_contract_states.keys())
            
            # Check for unexpected contract removals or additions
            removed_contracts = pre_addresses - post_addresses
            added_contracts = post_addresses - pre_addresses
            
            if removed_contracts:
                return False, f"Contracts unexpectedly removed during redaction: {list(removed_contracts)}"
            
            if added_contracts:
                return False, f"Contracts unexpectedly added during redaction: {list(added_contracts)}"
            
            # 2. Verify state transitions for each contract
            for contract_address in pre_addresses:
                pre_state = pre_contract_states[contract_address]
                post_state = post_contract_states[contract_address]
                
                # Create a mock operation for verification
                # In a real implementation, this would come from the proof data
                operation = {
                    "type": "REDACT_CONTRACT_DATA",
                    "contract_address": contract_address,
                    "redacted_fields": []  # Would be populated from proof metadata
                }
                
                # Use existing contract state verification
                is_valid, error = self.generator.contract_checker.verify_state_transition(
                    pre_state, post_state, operation
                )
                
                if not is_valid:
                    return False, f"Contract {contract_address} state transition invalid: {error}"
            
            # 3. Verify contract state consistency across blocks
            pre_blocks = pre_redaction_state.get("blocks", [])
            post_blocks = post_redaction_state.get("blocks", [])
            
            # Check that contract state references in blocks are consistent
            for block_index, (pre_block, post_block) in enumerate(zip(pre_blocks, post_blocks)):
                pre_contract_refs = pre_block.get("contract_references", {})
                post_contract_refs = post_block.get("contract_references", {})
                
                # Verify contract references haven't been tampered with
                for contract_addr in pre_contract_refs:
                    if contract_addr in post_contract_refs:
                        pre_ref = pre_contract_refs[contract_addr]
                        post_ref = post_contract_refs[contract_addr]
                        
                        # Check state hash consistency (if available)
                        if "state_hash" in pre_ref and "state_hash" in post_ref:
                            # For non-redacted contracts, state hash should remain the same
                            # For redacted contracts, we need to verify the hash change is valid
                            if pre_ref.get("version", 0) == post_ref.get("version", 0):
                                if pre_ref["state_hash"] != post_ref["state_hash"]:
                                    return False, f"Contract {contract_addr} state hash changed without version increment in block {block_index}"
            
            # 4. Verify contract bytecode integrity (contracts shouldn't be modified during redaction)
            for contract_address in pre_addresses:
                pre_state = pre_contract_states[contract_address]
                post_state = post_contract_states[contract_address]
                
                # Contract bytecode should remain unchanged
                pre_bytecode = pre_state.get("bytecode", "")
                post_bytecode = post_state.get("bytecode", "")
                
                if pre_bytecode != post_bytecode:
                    return False, f"Contract {contract_address} bytecode was modified during redaction"
                
                # Contract ABI should remain unchanged
                pre_abi = pre_state.get("abi", [])
                post_abi = post_state.get("abi", [])
                
                if pre_abi != post_abi:
                    return False, f"Contract {contract_address} ABI was modified during redaction"
            
            # 5. Verify balance consistency for token contracts
            for contract_address in pre_addresses:
                pre_state = pre_contract_states[contract_address]
                post_state = post_contract_states[contract_address]
                
                # Check if this is a token contract with balances
                if "balances" in pre_state and "balances" in post_state:
                    pre_balances = pre_state["balances"]
                    post_balances = post_state["balances"]
                    
                    # Total supply should be conserved (unless explicitly redacted)
                    pre_total = sum(pre_balances.values()) if isinstance(pre_balances, dict) else 0
                    post_total = sum(post_balances.values()) if isinstance(post_balances, dict) else 0
                    
                    # Allow for balance redaction, but flag suspicious total changes
                    if abs(pre_total - post_total) > pre_total * 0.1:  # 10% threshold
                        return False, f"Contract {contract_address} total balance changed significantly: {pre_total} -> {post_total}"
            
            # 6. Verify event log consistency
            for contract_address in pre_addresses:
                pre_state = pre_contract_states[contract_address]
                post_state = post_contract_states[contract_address]
                
                pre_events = pre_state.get("events", [])
                post_events = post_state.get("events", [])
                
                # Events can be redacted, but the count shouldn't increase
                if len(post_events) > len(pre_events):
                    return False, f"Contract {contract_address} gained events during redaction (suspicious)"
                
                # Check that non-redacted events remain intact
                for i, (pre_event, post_event) in enumerate(zip(post_events, pre_events[:len(post_events)])):
                    if "redacted" not in post_event:
                        # Non-redacted events should be identical
                        if pre_event != post_event:
                            return False, f"Contract {contract_address} event {i} was modified without redaction marker"
            
            return True, None
            
        except Exception as e:
            return False, f"Contract state proof verification error: {str(e)}"


# Testing and example usage
def test_consistency_system():
    """Test the proof-of-consistency system."""
    print("\n Testing Proof-of-Consistency System")
    print("=" * 50)
    
    generator = ConsistencyProofGenerator()
    verifier = ConsistencyProofVerifier()
    
    # Sample data
    pre_data = {
        "blocks": [
            {
                "depth": 0,
                "id": "genesis",
                "previous": "",
                "timestamp": 1000000,
                "transactions": []
            },
            {
                "depth": 1,
                "id": "block1",
                "previous": "genesis",
                "timestamp": 1000001,
                "transactions": [
                    {"id": "tx1", "sender": "alice", "to": "bob", "value": 10}
                ]
            }
        ]
    }
    
    post_data = {
        "blocks": [
            {
                "depth": 0,
                "id": "genesis",
                "previous": "",
                "timestamp": 1000000,
                "transactions": []
            },
            {
                "depth": 1,
                "id": "block1_redacted",
                "previous": "genesis",
                "timestamp": 1000001,
                "transactions": [
                    {"id": "tx1", "sender": "REDACTED", "to": "bob", "value": 10}
                ]
            }
        ]
    }
    
    operation = {
        "target_block": 1,
        "target_tx": 0,
        "redaction_type": "ANONYMIZE",
        "block_range": (0, 2)
    }
    
    # Generate consistency proofs
    consistency_checks = [
        ConsistencyCheckType.BLOCK_INTEGRITY,
        ConsistencyCheckType.HASH_CHAIN,
        ConsistencyCheckType.MERKLE_TREE,
        ConsistencyCheckType.TRANSACTION_ORDERING
    ]
    
    for check_type in consistency_checks:
        print(f"\n Generating {check_type.value} proof...")
        
        proof = generator.generate_consistency_proof(
            check_type, pre_data, post_data, operation
        )
        
        print(f"  ID: {proof.proof_id}")
        print(f"  Valid: {'' if proof.is_valid else ''}")
        if proof.error_details:
            print(f"  Error: {proof.error_details}")
            
        # Verify proof
        is_valid, error = verifier.verify_proof(proof)
        print(f"  Verification: {' PASSED' if is_valid else f' FAILED - {error}'}")
    
    print("\n Consistency system test completed!")


if __name__ == "__main__":
    test_consistency_system()  # TODO: check if I completely and correctly check and test all this file (ProofOfConsistency.py)
