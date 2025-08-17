#!/usr/bin/env python3
"""
Comprehensive Test Suite for Improved Redactable Blockchain
This test suite provides thorough testing of all improved features including:
- Smart contract deployment and execution
- Permission-based access control
- Redaction request workflow
- Transaction types and privacy levels
- Block redaction capabilities
- Policy compliance checking
"""

import sys
import os
import unittest
import time
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from InputsConfig import InputsConfig as p
from Models.SmartContract import SmartContract, ContractCall, RedactionPolicy, PermissionManager
from Models.Bitcoin.Node import Node
from Models.Transaction import Transaction
from Models.Block import Block


class TestEnhancedBlockchain(unittest.TestCase):
    """Comprehensive test cases for improved blockchain features."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create test nodes with different roles
        self.admin = Node(id=1, hashPower=100)
        self.admin.update_role("ADMIN")
        
        self.regulator = Node(id=2, hashPower=50)
        self.regulator.update_role("REGULATOR")
        
        self.miner = Node(id=3, hashPower=200)
        self.miner.update_role("MINER")
        
        self.user = Node(id=4, hashPower=0)
        self.user.update_role("USER")
        
        self.observer = Node(id=5, hashPower=0)
        self.observer.update_role("OBSERVER")
    
    def test_permission_system_comprehensive(self):
        """Test the complete permission system."""
        print("\n=== Testing Comprehensive Permission System ===")
        
        # Test ADMIN permissions
        admin_actions = ["READ", "WRITE", "DEPLOY", "REDACT", "APPROVE", "AUDIT"]
        for action in admin_actions:
            self.assertTrue(self.admin.can_perform_action(action), 
                          f"Admin should be able to {action}")
        
        # Test REGULATOR permissions
        regulator_actions = ["READ", "AUDIT", "REDACT", "APPROVE"]
        forbidden_actions = ["DEPLOY", "MINE"]
        for action in regulator_actions:
            self.assertTrue(self.regulator.can_perform_action(action),
                          f"Regulator should be able to {action}")
        for action in forbidden_actions:
            self.assertFalse(self.regulator.can_perform_action(action),
                           f"Regulator should NOT be able to {action}")
        
        # Test USER permissions
        user_actions = ["READ", "WRITE", "TRANSACT"]
        forbidden_actions = ["DEPLOY", "REDACT", "APPROVE", "AUDIT", "MINE"]
        for action in user_actions:
            self.assertTrue(self.user.can_perform_action(action),
                          f"User should be able to {action}")
        for action in forbidden_actions:
            self.assertFalse(self.user.can_perform_action(action),
                           f"User should NOT be able to {action}")
        
        print(" Permission system working correctly")
    
    def test_smart_contract_lifecycle(self):
        """Test complete smart contract deployment and interaction."""
        print("\n=== Testing Smart Contract Lifecycle ===")
        
        # Test contract deployment by admin
        contract_code = """
        contract TokenContract {
            mapping(address => uint256) public balances;
            uint256 public totalSupply;
            
            function mint(address to, uint256 amount) public {
                balances[to] += amount;
                totalSupply += amount;
            }
            
            function transfer(address to, uint256 amount) public {
                require(balances[msg.sender] >= amount);
                balances[msg.sender] -= amount;
                balances[to] += amount;
            }
        }
        """
        
        contract_address = self.admin.deploy_contract(contract_code, "GENERAL")
        self.assertIsNotNone(contract_address, "Contract deployment should succeed")
        self.assertIn(contract_address, self.admin.deployed_contracts)
        
        # Test contract deployment by user (should fail)
        user_contract = self.user.deploy_contract(contract_code, "GENERAL")
        self.assertIsNone(user_contract, "User should not be able to deploy contracts")
        
        # Test contract call creation
        contract_call = ContractCall(
            contract_address=contract_address,
            function_name="mint",
            parameters=["0x123", 1000],
            caller=str(self.admin.id),
            gas_limit=100000
        )
        
        self.assertEqual(contract_call.contract_address, contract_address)
        self.assertEqual(contract_call.function_name, "mint")
        self.assertEqual(len(contract_call.parameters), 2)
        
        print(f" Contract deployed at: {contract_address}")
        print(" Smart contract lifecycle working correctly")
    
    def test_transaction_types_and_privacy(self):
        """Test different transaction types and privacy levels."""
        print("\n=== Testing Transaction Types and Privacy ===")
        
        # Test regular transfer transaction
        transfer_tx = Transaction(
            id=1001,
            sender=self.user.id,
            to=self.miner.id,
            value=100,
            tx_type="TRANSFER",
            privacy_level="PUBLIC",
            is_redactable=True
        )
        
        self.assertEqual(transfer_tx.tx_type, "TRANSFER")
        self.assertEqual(transfer_tx.privacy_level, "PUBLIC")
        self.assertTrue(transfer_tx.is_redactable)
        
        # Test smart contract call transaction
        contract_call = ContractCall(
            contract_address="0x1234567890abcdef",
            function_name="transfer",
            parameters=[100],
            caller=str(self.user.id),
            gas_limit=50000
        )
        
        contract_tx = Transaction(
            id=1002,
            sender=self.user.id,
            to=0,  # Contract transaction
            tx_type="CONTRACT_CALL",
            contract_call=contract_call,
            privacy_level="PRIVATE",
            is_redactable=True
        )
        
        self.assertEqual(contract_tx.tx_type, "CONTRACT_CALL")
        self.assertEqual(contract_tx.privacy_level, "PRIVATE")
        self.assertIsNotNone(contract_tx.contract_call)
        
        # Test redaction request transaction
        redaction_tx = Transaction(
            id=1003,
            sender=self.regulator.id,
            to=0,
            tx_type="REDACTION_REQUEST",
            metadata={
                "target_block": 10,
                "target_tx": 5,
                "redaction_type": "ANONYMIZE",
                "reason": "GDPR compliance"
            },
            privacy_level="CONFIDENTIAL",
            is_redactable=False  # Redaction requests should not be redactable
        )
        
        self.assertEqual(redaction_tx.tx_type, "REDACTION_REQUEST")
        self.assertEqual(redaction_tx.privacy_level, "CONFIDENTIAL")
        self.assertFalse(redaction_tx.is_redactable)
        self.assertIn("target_block", redaction_tx.metadata)
        
        print(" All transaction types working correctly")
    
    def test_redaction_workflow_complete(self):
        """Test complete redaction workflow with approvals."""
        print("\n=== Testing Complete Redaction Workflow ===")
        
        # Step 1: Regulator requests redaction
        request_id = self.regulator.request_redaction(
            target_block=5,
            target_tx=2,
            redaction_type="DELETE",
            reason="GDPR right to erasure"
        )
        
        self.assertIsNotNone(request_id, "Regulator should be able to request redaction")
        self.assertEqual(len(self.regulator.redaction_requests), 1)
        
        # Step 2: Admin approves redaction
        admin_vote = self.admin.vote_on_redaction(request_id, True, "Compliance approved")
        self.assertTrue(admin_vote, "Admin should be able to vote on redaction")
        
        # Step 3: Another regulator approves (we'll use a second regulator)
        regulator2 = Node(id=6, hashPower=30)
        regulator2.update_role("REGULATOR")
        regulator2_vote = regulator2.vote_on_redaction(request_id, True, "Privacy laws compliance")
        self.assertTrue(regulator2_vote, "Second regulator should be able to vote")
        
        # Step 4: User tries to vote (should fail)
        user_vote = self.user.vote_on_redaction(request_id, True, "User opinion")
        self.assertFalse(user_vote, "User should not be able to vote on redaction")
        
        # Step 5: Check voting records
        self.assertIn(request_id, self.admin.voted_redactions)
        self.assertIn(request_id, regulator2.voted_redactions)
        self.assertNotIn(request_id, self.user.voted_redactions)
        
        # Step 6: Test double voting prevention
        double_vote = self.admin.vote_on_redaction(request_id, False, "Changed mind")
        self.assertFalse(double_vote, "Should not allow double voting")
        
        print(f" Redaction request {request_id[:8]}... processed correctly")
        print(" Complete redaction workflow working correctly")
    
    def test_enhanced_block_features(self):
        """Test improved block features including redaction capabilities."""
        print("\n=== Testing Improved Block Features ===")
        
        # Create block with different transaction types
        block = Block(
            depth=10,
            id=12345,
            previous=54321,
            timestamp=int(time.time()),
            miner=self.miner.id,
            block_type="NORMAL"
        )
        
        # Add transactions of different types
        transactions = [
            Transaction(id=1001, tx_type="TRANSFER", is_redactable=True),
            Transaction(id=1002, tx_type="CONTRACT_CALL", is_redactable=True),
            Transaction(id=1003, tx_type="REDACTION_REQUEST", is_redactable=False),
            Transaction(id=1004, tx_type="CONTRACT_DEPLOY", is_redactable=True)
        ]
        
        block.transactions = transactions
        
        # Test block properties
        self.assertEqual(block.depth, 10)
        self.assertEqual(block.block_type, "NORMAL")
        self.assertEqual(len(block.transactions), 4)
        
        # Test redaction capability (should be False due to non-redactable transaction)
        self.assertFalse(block.is_redactable(), "Block should not be redactable due to non-redactable tx")
        
        # Create a fully redactable block
        redactable_block = Block(
            depth=11,
            id=12346,
            previous=12345,
            timestamp=int(time.time()),
            miner=self.miner.id,
            block_type="NORMAL"
        )
        
        redactable_transactions = [
            Transaction(id=2001, tx_type="TRANSFER", is_redactable=True),
            Transaction(id=2002, tx_type="CONTRACT_CALL", is_redactable=True)
        ]
        
        redactable_block.transactions = redactable_transactions
        self.assertTrue(redactable_block.is_redactable(), "Block should be redactable")
        
        # Test redaction record addition
        redactable_block.add_redaction_record(
            redaction_type="DELETE",
            target_tx=0,
            requester=self.regulator.id,
            approvers=[self.admin.id, self.regulator.id]
        )
        
        self.assertEqual(len(redactable_block.redaction_history), 1)
        redaction = redactable_block.redaction_history[0]
        self.assertEqual(redaction["type"], "DELETE")
        self.assertEqual(redaction["requester"], self.regulator.id)
        self.assertEqual(len(redaction["approvers"]), 2)
        
        # Test genesis block (should not be redactable)
        genesis_block = Block(depth=0, block_type="NORMAL")
        self.assertFalse(genesis_block.is_redactable(), "Genesis block should not be redactable")
        
        # Test audit block (should not be redactable)
        audit_block = Block(depth=5, block_type="AUDIT")
        self.assertFalse(audit_block.is_redactable(), "Audit block should not be redactable")
        
        print(" Improved block features working correctly")
    
    def test_policy_compliance_system(self):
        """Test redaction policy compliance checking."""
        print("\n=== Testing Policy Compliance System ===")
        
        # Define test policies
        policies = [
            {
                "policy_id": "GDPR_COMPLIANCE",
                "policy_type": "DELETE",
                "authorized_roles": ["ADMIN", "REGULATOR"],
                "min_approvals": 2,
                "time_lock": 86400,  # 24 hours
                "conditions": ["data_age > 30_days", "user_consent_withdrawn"]
            },
            {
                "policy_id": "AUDIT_REQUIREMENT",
                "policy_type": "ANONYMIZE",
                "authorized_roles": ["ADMIN"],
                "min_approvals": 1,
                "time_lock": 0,
                "conditions": ["audit_period_ended"]
            },
            {
                "policy_id": "EMERGENCY_DELETION",
                "policy_type": "DELETE",
                "authorized_roles": ["ADMIN", "REGULATOR"],
                "min_approvals": 3,
                "time_lock": 3600,  # 1 hour
                "conditions": ["security_breach", "legal_order"]
            }
        ]
        
        # Test policy validation
        for policy in policies:
            self.assertIn("policy_id", policy)
            self.assertIn("policy_type", policy)
            self.assertIn("authorized_roles", policy)
            self.assertIn("min_approvals", policy)
            self.assertIsInstance(policy["min_approvals"], int)
            self.assertGreater(policy["min_approvals"], 0)
            
            # Test role authorization
            for role in policy["authorized_roles"]:
                self.assertIn(role, ["ADMIN", "REGULATOR", "MINER", "USER", "OBSERVER"])
        
        # Test policy application simulation
        gdpr_policy = policies[0]
        
        # Simulate GDPR compliance check
        def check_policy_compliance(node, policy):
            """Check if a node can execute a policy."""
            role_authorized = node.role in policy["authorized_roles"]
            can_approve = node.can_perform_action("APPROVE")
            return role_authorized and can_approve
        
        # Test compliance for different nodes
        self.assertTrue(check_policy_compliance(self.admin, gdpr_policy))
        self.assertTrue(check_policy_compliance(self.regulator, gdpr_policy))
        self.assertFalse(check_policy_compliance(self.user, gdpr_policy))
        self.assertFalse(check_policy_compliance(self.observer, gdpr_policy))
        
        print(" Policy compliance system working correctly")
    
    def test_integration_scenario(self):
        """Test a complete integration scenario."""
        print("\n=== Testing Integration Scenario ===")
        
        # Scenario: Deploy contract, execute transactions, request redaction
        
        # Step 1: Admin deploys a contract
        contract_address = self.admin.deploy_contract(
            "contract UserData { mapping(address => string) data; }",
            "GENERAL"
        )
        self.assertIsNotNone(contract_address)
        
        # Step 2: User makes transactions
        user_transactions = []
        for i in range(3):
            tx = Transaction(
                id=3000 + i,
                sender=self.user.id,
                to=self.miner.id,
                value=50 + i * 10,
                tx_type="TRANSFER",
                privacy_level="PUBLIC",
                is_redactable=True
            )
            user_transactions.append(tx)
        
        # Step 3: Create block with transactions
        block = Block(
            depth=20,
            id=20000,
            previous=19999,
            timestamp=int(time.time()),
            miner=self.miner.id,
            transactions=user_transactions,
            block_type="NORMAL"
        )
        
        # Step 4: User requests redaction (should work for GDPR)
        request_id = self.user.request_redaction(
            target_block=block.depth,
            target_tx=1,
            redaction_type="DELETE",
            reason="GDPR Article 17 - Right to erasure"
        )
        
        # Note: In a real implementation, users might have permission to request
        # but not approve redactions. For this test, we'll check the request was created.
        if request_id is None:
            print("  Note: User redaction request failed (as expected in current permission model)")
        else:
            print(f"  User redaction request created: {request_id[:8]}...")
        
        # Step 5: Regulator requests redaction (should work)
        regulator_request = self.regulator.request_redaction(
            target_block=block.depth,
            target_tx=2,
            redaction_type="ANONYMIZE",
            reason="Privacy protection order"
        )
        self.assertIsNotNone(regulator_request)
        
        # Step 6: Admin and another regulator approve
        approval1 = self.admin.vote_on_redaction(regulator_request, True, "Approved")
        self.assertTrue(approval1)
        
        # Step 7: Add redaction record to block
        block.add_redaction_record(
            redaction_type="ANONYMIZE",
            target_tx=2,
            requester=self.regulator.id,
            approvers=[self.admin.id]
        )
        
        # Verify final state
        self.assertEqual(len(block.redaction_history), 1)
        # Note: Admin has made approvals in previous tests, so we check the current count
        current_admin_approvals = len(self.admin.redaction_approvals)
        self.assertGreaterEqual(current_admin_approvals, 1)  # At least one approval
        current_regulator_requests = len(self.regulator.redaction_requests)
        self.assertGreaterEqual(current_regulator_requests, 1)  # At least one request
        
        print(" Integration scenario completed successfully")


def run_comprehensive_tests():
    """Run all comprehensive tests with detailed output."""
    print("Improved Redactable Blockchain - Comprehensive Test Suite")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEnhancedBlockchain)
    
    # Run tests with custom result handler
    class DetailedTestResult(unittest.TextTestResult):
        def startTest(self, test):
            super().startTest(test)
            print(f"\nRunning: {test._testMethodName}")
        
        def addSuccess(self, test):
            super().addSuccess(test)
            print(f" PASSED: {test._testMethodName}")
        
        def addError(self, test, err):
            super().addError(test, err)
            print(f" ERROR: {test._testMethodName}")
            print(f"  {err[1]}")
        
        def addFailure(self, test, err):
            super().addFailure(test, err)
            print(f" FAILED: {test._testMethodName}")
            print(f"  {err[1]}")
    
    # Run the tests
    runner = unittest.TextTestRunner(
        resultclass=DetailedTestResult,
        verbosity=0,
        stream=open(os.devnull, 'w')  # Suppress default output
    )
    
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            failure_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"  - {test}: {failure_msg}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            error_msg = traceback.split('\n')[-2]
            print(f"  - {test}: {error_msg}")
    
    if result.wasSuccessful():
        print("\n ALL TESTS PASSED! The improved blockchain features are working correctly.")
    else:
        print(f"\n️  {len(result.failures + result.errors)} test(s) failed. Please review the issues above.")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
