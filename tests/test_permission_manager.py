#!/usr/bin/env python3
import unittest

from Models.SmartContract import PermissionManager


class TestPermissionManager(unittest.TestCase):
    def test_assign_and_check_permissions(self):
        pm = PermissionManager()

        # Assign roles
        self.assertTrue(pm.assign_role(1, "ADMIN"))
        self.assertTrue(pm.assign_role(2, "USER"))
        self.assertTrue(pm.assign_role(3, "REGULATOR"))
        self.assertFalse(pm.assign_role(4, "NON_EXISTENT_ROLE"))

        # Generic permissions
        self.assertTrue(pm.check_permission(1, "REDACT"))
        self.assertFalse(pm.check_permission(2, "REDACT"))
        self.assertTrue(pm.check_permission(3, "AUDIT"))

        # Contract-specific permissions
        contract = "0xABC"
        pm.contract_permissions[contract] = {"EXECUTE": [42]}
        self.assertFalse(pm.check_permission(42, "EXECUTE"))  # no resource provided
        self.assertTrue(pm.check_permission(42, "EXECUTE", resource=contract))
        self.assertFalse(pm.check_permission(43, "EXECUTE", resource=contract))

    def test_get_role_level(self):
        pm = PermissionManager()
        self.assertEqual(pm.get_role_level(99), 0)  # no role
        pm.assign_role(5, "MINER")
        self.assertGreater(pm.get_role_level(5), 0)


if __name__ == "__main__":
    unittest.main()
