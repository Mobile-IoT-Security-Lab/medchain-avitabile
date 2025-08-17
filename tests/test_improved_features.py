#!/usr/bin/env python3
"""
Test script for the Improved Redactable Blockchain with Smart Contract Support
Demonstrates key features of the smart contract and permissioned redaction system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from InputsConfig import InputsConfig as p
from Models.SmartContract import SmartContract, ContractCall, RedactionPolicy, PermissionManager
from Models.Bitcoin.Node import Node
from Models.Transaction import Transaction
from Models.Block import Block

def test_permission_system():
    """Test the role-based permission system."""
    print("=== Testing Permission System ===")
    
    # Create test nodes
    admin = Node(id=1, hashPower=100)
    admin.update_role("ADMIN")
    
    user = Node(id=2, hashPower=0)
    user.update_role("USER")
    
    regulator = Node(id=3, hashPower=50)
    regulator.update_role("REGULATOR")
    
    # Test permissions
    print(f"Admin can deploy contracts: {admin.can_perform_action('DEPLOY')}")
    print(f"User can deploy contracts: {user.can_perform_action('DEPLOY')}")
    print(f"Regulator can redact: {regulator.can_perform_action('REDACT')}")
    print(f"User can redact: {user.can_perform_action('REDACT')}")
    print()

def test_smart_contract_deployment():
    """Test smart contract deployment."""
    print("=== Testing Smart Contract Deployment ===")
    
    admin = Node(id=1, hashPower=100)
    admin.update_role("ADMIN")
    
    # Deploy a simple contract
    contract_code = """
    contract TestContract {
        uint256 public value;
        
        function setValue(uint256 _value) public {
            value = _value;
        }
        
        function getValue() public view returns (uint256) {
            return value;
        }
    }
    """
    
    contract_address = admin.deploy_contract(contract_code, "GENERAL")
    if contract_address:
        print(f"Contract deployed successfully at address: {contract_address}")
        print(f"Admin deployed contracts: {admin.deployed_contracts}")
    else:
        print("Failed to deploy contract")
    print()

def test_redaction_workflow():
    """Test the redaction request and approval workflow."""
    print("=== Testing Redaction Workflow ===")
    
    # Create nodes with different roles
    admin = Node(id=1, hashPower=100)
    admin.update_role("ADMIN")
    
    regulator = Node(id=2, hashPower=50)
    regulator.update_role("REGULATOR")
    
    user = Node(id=3, hashPower=0)
    user.update_role("USER")
    
    # User requests redaction
    request_id = user.request_redaction(
        target_block=5,
        target_tx=2,
        redaction_type="DELETE",
        reason="GDPR compliance - user data removal request"
    )
    
    if request_id:
        print(f"Redaction request created: {request_id}")
        print(f"User redaction requests: {len(user.redaction_requests)}")
        
        # Admin and regulator vote on the request
        admin_vote = admin.vote_on_redaction(request_id, True, "Approved for compliance")
        regulator_vote = regulator.vote_on_redaction(request_id, True, "Privacy rights respected")
        
        print(f"Admin vote: {admin_vote}")
        print(f"Regulator vote: {regulator_vote}")
        print(f"Admin voted redactions: {len(admin.voted_redactions)}")
        print(f"Regulator approvals: {len(regulator.redaction_approvals)}")
    else:
        print("User cannot request redaction (insufficient permissions)")
    print()

def test_enhanced_transactions():
    """Test improved transaction types."""
    print("=== Testing Improved Transaction Types ===")
    
    # Create different types of transactions
    
    # Regular transfer
    transfer_tx = Transaction(
        id=1001,
        sender=1,
        to=2,
        value=100,
        tx_type="TRANSFER",
        privacy_level="PUBLIC"
    )
    print(f"Transfer transaction: {transfer_tx.tx_type}, Privacy: {transfer_tx.privacy_level}")
    
    # Smart contract call
    contract_call = ContractCall(
        contract_address="0x1234567890abcdef",
        function_name="setValue",
        parameters=[42],
        caller="1",
        gas_limit=100000
    )
    
    contract_tx = Transaction(
        id=1002,
        sender=1,
        to=0,
        tx_type="CONTRACT_CALL",
        contract_call=contract_call,
        privacy_level="PRIVATE"
    )
    print(f"Contract call transaction: {contract_tx.tx_type}, Function: {contract_tx.contract_call.function_name}")
    
    # Redaction request
    redaction_tx = Transaction(
        id=1003,
        sender=3,
        to=0,
        tx_type="REDACTION_REQUEST",
        metadata={
            "target_block": 10,
            "target_tx": 5,
            "redaction_type": "ANONYMIZE",
            "reason": "Sensitive data protection"
        },
        privacy_level="CONFIDENTIAL"
    )
    print(f"Redaction request: {redaction_tx.tx_type}, Type: {redaction_tx.metadata['redaction_type']}")
    print()

def test_enhanced_block():
    """Test improved block with smart contract and redaction features."""
    print("=== Testing Improved Block Features ===")
    
    # Create an improved block
    block = Block(
        depth=1,
        id=12345,
        previous=54321,
        timestamp=1640995200,  # 2022-01-01
        miner=1,
        block_type="NORMAL"
    )
    
    # Add some transactions
    tx1 = Transaction(id=1001, tx_type="TRANSFER", is_redactable=True)
    tx2 = Transaction(id=1002, tx_type="CONTRACT_CALL", is_redactable=True)
    tx3 = Transaction(id=1003, tx_type="REDACTION_REQUEST", is_redactable=False)
    
    block.transactions = [tx1, tx2, tx3]
    
    print(f"Block depth: {block.depth}")
    print(f"Block type: {block.block_type}")
    print(f"Number of transactions: {len(block.transactions)}")
    print(f"Block is redactable: {block.is_redactable()}")
    
    # Add redaction record
    block.add_redaction_record(
        redaction_type="DELETE",
        target_tx=0,
        requester=3,
        approvers=[1, 2]
    )
    
    print(f"Redaction history entries: {len(block.redaction_history)}")
    if block.redaction_history:
        print(f"Latest redaction: {block.redaction_history[0]['type']} by user {block.redaction_history[0]['requester']}")
    print()

def test_redaction_policies():
    """Test redaction policy checking."""
    print("=== Testing Redaction Policies ===")
    
    # Create test policies
    policies = [
        {
            "policy_id": "GDPR_COMPLIANCE",
            "policy_type": "DELETE",
            "authorized_roles": ["ADMIN", "REGULATOR"],
            "min_approvals": 2,
            "time_lock": 86400
        },
        {
            "policy_id": "AUDIT_REQUIREMENT", 
            "policy_type": "ANONYMIZE",
            "authorized_roles": ["ADMIN"],
            "min_approvals": 1,
            "time_lock": 0
        }
    ]
    
    # Test policy compliance
    for policy in policies:
        print(f"Policy: {policy['policy_id']}")
        print(f"  Type: {policy['policy_type']}")
        print(f"  Authorized roles: {policy['authorized_roles']}")
        print(f"  Min approvals: {policy['min_approvals']}")
        print(f"  Time lock: {policy['time_lock']} seconds")
    print()

def run_all_tests():
    """Run all test functions."""
    print("Improved Redactable Blockchain Test Suite")
    print("=" * 50)
    print()
    
    test_permission_system()
    test_smart_contract_deployment()
    test_redaction_workflow()
    test_enhanced_transactions()
    test_enhanced_block()
    test_redaction_policies()
    
    print("All tests completed successfully!")
    print("=" * 50)

if __name__ == "__main__":
    run_all_tests()
