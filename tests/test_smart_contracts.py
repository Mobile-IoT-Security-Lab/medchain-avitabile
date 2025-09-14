#!/usr/bin/env python3
"""
Unit tests focused exclusively on smart-contract classes and helpers.

Covers:
- ContractExecutionEngine deployment and call execution (gas, logging)
- RedactionPolicy configuration in MedicalDataContract
- Policy-derived approval thresholds in MyRedactionEngine
- PermissionManager contract-specific permissions
"""

import sys
import os
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Models.SmartContract import (
    SmartContract,
    ContractCall,
    ContractExecutionEngine,
    PermissionManager,
)
from medical.MedicalRedactionEngine import MyRedactionEngine


class TestContractExecutionEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ContractExecutionEngine()

    def test_deploy_and_execute_success(self):
        contract = SmartContract(code="contract X {}", is_redactable=False)
        addr = self.engine.deploy_contract(contract)
        self.assertTrue(addr)
        self.assertIn(addr, self.engine.deployed_contracts)

        # Create a call with enough gas
        call = ContractCall(
            contract_address=addr,
            function_name="setValue",
            parameters=[123],
            caller="0xabc",
            gas_limit=50000,
        )
        ok = self.engine.execute_call(call, timestamp=0)
        self.assertTrue(ok)
        self.assertTrue(call.success)
        self.assertGreater(call.gas_used, 0)
        self.assertLessEqual(call.gas_used, call.gas_limit)
        self.assertTrue(len(self.engine.execution_logs) >= 1)

    def test_execute_fails_for_unknown_or_out_of_gas(self):
        # Unknown contract address
        bad_call = ContractCall(contract_address="0xdead", function_name="f", parameters=[], gas_limit=1000)
        ok = self.engine.execute_call(bad_call, timestamp=0)
        self.assertFalse(ok)
        self.assertFalse(bad_call.success)

        # Out of gas (long function name + many params will exceed small limit)
        contract = SmartContract(code="contract Y {}")
        addr = self.engine.deploy_contract(contract)
        heavy_call = ContractCall(
            contract_address=addr,
            function_name="veryExpensiveFunctionName",
            parameters=[1, 2, 3, 4, 5, 6, 7],
            gas_limit=21000,  # base cost; should be too small
        )
        ok2 = self.engine.execute_call(heavy_call, timestamp=0)
        self.assertFalse(ok2)
        self.assertFalse(heavy_call.success)


class TestRedactionPolicies(unittest.TestCase):
    def setUp(self):
        self.redaction = MyRedactionEngine()
        self.contract = self.redaction.medical_contract

    def test_medical_contract_policies(self):
        self.assertTrue(self.contract.is_redactable)
        policies = getattr(self.contract, "redaction_policies", [])
        self.assertEqual(len(policies), 3)

        policy_types = {p.policy_type: p for p in policies}
        self.assertIn("DELETE", policy_types)
        self.assertIn("ANONYMIZE", policy_types)
        self.assertIn("MODIFY", policy_types)

        self.assertEqual(policy_types["DELETE"].min_approvals, 2)
        self.assertEqual(policy_types["ANONYMIZE"].min_approvals, 3)
        self.assertEqual(policy_types["MODIFY"].min_approvals, 1)

    def test_policy_driven_thresholds(self):
        self.assertEqual(self.redaction._get_approval_threshold("DELETE"), 2)
        self.assertEqual(self.redaction._get_approval_threshold("ANONYMIZE"), 3)
        self.assertEqual(self.redaction._get_approval_threshold("MODIFY"), 1)


class TestPermissionManagerContractSpecific(unittest.TestCase):
    def test_contract_specific_permissions(self):
        pm = PermissionManager()
        # Assign USER role that normally lacks "REDACT"
        pm.assign_role(10, "USER")
        self.assertFalse(pm.check_permission(10, "REDACT"))

        # Grant contract-specific permission for REDACT on a resource
        resource_addr = "0xCONTRACT"
        pm.contract_permissions[resource_addr] = {"REDACT": [10]}
        self.assertTrue(pm.check_permission(10, "REDACT", resource=resource_addr))


if __name__ == "__main__":
    unittest.main()
