import random
import hashlib


class SmartContract(object):
    """Defines a Smart Contract model for permissioned blockchain.
    
    :param str address: unique contract address
    :param str code: contract bytecode or source code
    :param dict state: contract state variables
    :param str owner: address of the contract owner
    :param dict permissions: permissions for different operations
    :param bool is_redactable: whether the contract allows redaction
    :param list redaction_policies: list of redaction policies
    """
    
    def __init__(self,
                 address="",
                 code="",
                 state=None,
                 owner="",
                 permissions=None,
                 is_redactable=False,
                 redaction_policies=None):
        self.address = address
        self.code = code
        self.state = state or {}
        self.owner = owner
        self.permissions = permissions or {}
        self.is_redactable = is_redactable
        self.redaction_policies = redaction_policies or []
        self.creation_timestamp = 0
        self.last_updated = 0


class ContractCall(object):
    """Defines a smart contract function call.
    
    :param str contract_address: address of the target contract
    :param str function_name: name of the function to call
    :param list parameters: function parameters
    :param str caller: address of the caller
    :param int gas_limit: maximum gas for execution
    :param int gas_used: actual gas consumed
    :param bool success: whether the call succeeded
    :param any return_value: return value of the function
    """
    
    def __init__(self,
                 contract_address="",
                 function_name="",
                 parameters=None,
                 caller="",
                 gas_limit=100000,
                 gas_used=0,
                 success=False,
                 return_value=None):
        self.contract_address = contract_address
        self.function_name = function_name
        self.parameters = parameters or []
        self.caller = caller
        self.gas_limit = gas_limit
        self.gas_used = gas_used
        self.success = success
        self.return_value = return_value


class RedactionPolicy(object):
    """Defines a redaction policy for smart contracts.
    
    :param str policy_id: unique policy identifier
    :param str policy_type: type of redaction (DELETE, MODIFY, ANONYMIZE)
    :param dict conditions: conditions for applying the policy
    :param list authorized_roles: roles authorized to execute this policy
    :param int min_approvals: minimum approvals required
    :param int time_lock: time lock period in seconds
    """
    
    def __init__(self,
                 policy_id="",
                 policy_type="DELETE",
                 conditions=None,
                 authorized_roles=None,
                 min_approvals=1,
                 time_lock=0):
        self.policy_id = policy_id
        self.policy_type = policy_type  # DELETE, MODIFY, ANONYMIZE
        self.conditions = conditions or {}
        self.authorized_roles = authorized_roles or []
        self.min_approvals = min_approvals
        self.time_lock = time_lock
        self.created_at = 0


class PermissionManager(object):
    """Manages permissions in the permissioned blockchain."""
    
    def __init__(self):
        self.roles = {
            "ADMIN": {"level": 100, "permissions": ["ALL"]},
            "REGULATOR": {"level": 80, "permissions": ["READ", "REDACT", "AUDIT"]},
            "MINER": {"level": 60, "permissions": ["READ", "MINE", "VALIDATE"]},
            "USER": {"level": 40, "permissions": ["READ", "TRANSACT"]},
            "OBSERVER": {"level": 20, "permissions": ["READ"]}
        }
        self.node_roles = {}  # node_id -> role
        self.contract_permissions = {}  # contract_address -> permissions
    
    def assign_role(self, node_id: int, role: str):
        """Assign a role to a node."""
        if role in self.roles:
            self.node_roles[node_id] = role
            return True
        return False
    
    def check_permission(self, node_id: int, action: str, resource: str = None) -> bool:
        """Check if a node has permission for an action."""
        if node_id not in self.node_roles:
            return False
        
        role = self.node_roles[node_id]
        permissions = self.roles[role]["permissions"]
        
        if "ALL" in permissions or action in permissions:
            return True
        
        # Check contract-specific permissions
        if resource and resource in self.contract_permissions:
            contract_perms = self.contract_permissions[resource]
            if node_id in contract_perms.get(action, []):
                return True
        
        return False
    
    def get_role_level(self, node_id: int) -> int:
        """Get the permission level of a node."""
        if node_id not in self.node_roles:
            return 0
        role = self.node_roles[node_id]
        return self.roles[role]["level"]


class ContractExecutionEngine(object):
    """Executes smart contract calls."""
    
    def __init__(self):
        self.deployed_contracts = {}  # address -> SmartContract
        self.execution_logs = []
        
    def deploy_contract(self, contract: SmartContract) -> str:
        """Deploy a new smart contract."""
        if not contract.address:
            contract.address = self._generate_contract_address()
        
        self.deployed_contracts[contract.address] = contract
        return contract.address
    
    def execute_call(self, call: ContractCall, timestamp: int) -> bool:
        """Execute a contract function call."""
        if call.contract_address not in self.deployed_contracts:
            call.success = False
            return False
        
        contract = self.deployed_contracts[call.contract_address]
        
        # Simulate contract execution
        gas_cost = self._calculate_gas_cost(call)
        if gas_cost > call.gas_limit:
            call.success = False
            return False
        
        call.gas_used = gas_cost
        call.success = True
        
        # Log the execution
        self.execution_logs.append({
            "timestamp": timestamp,
            "contract": call.contract_address,
            "function": call.function_name,
            "caller": call.caller,
            "gas_used": call.gas_used
        })
        
        return True
    
    def _generate_contract_address(self) -> str:
        """Generate a unique contract address."""
        return hashlib.sha256(str(random.random()).encode()).hexdigest()[:40]
    
    def _calculate_gas_cost(self, call: ContractCall) -> int:
        """Calculate gas cost for a contract call."""
        base_cost = 21000
        function_cost = len(call.function_name) * 100
        param_cost = len(call.parameters) * 200
        return base_cost + function_cost + param_cost


# Predefined smart contracts for redaction scenarios

class RedactionAuditContract(SmartContract):
    """A smart contract for auditing redaction operations."""
    
    def __init__(self):
        super().__init__(
            code="""
            contract RedactionAudit {
                mapping(bytes32 => RedactionRecord) public redactions;
                
                struct RedactionRecord {
                    address requester;
                    uint256 timestamp;
                    string reason;
                    bytes32 originalHash;
                    bytes32 newHash;
                    bool approved;
                }
                
                function requestRedaction(bytes32 _id, string _reason) public;
                function approveRedaction(bytes32 _id) public;
                function getRedactionRecord(bytes32 _id) public view returns (RedactionRecord);
            }
            """,
            is_redactable=False,  # Audit contract should not be redactable
            permissions={"READ": ["ALL"], "REDACT": ["ADMIN", "REGULATOR"]}
        )


class DataPrivacyContract(SmartContract):
    """A smart contract for managing data privacy policies."""
    
    def __init__(self):
        super().__init__(
            code="""
            contract DataPrivacy {
                mapping(address => PrivacyPolicy) public policies;
                
                struct PrivacyPolicy {
                    uint256 retentionPeriod;
                    bool allowRedaction;
                    address[] authorizedRedactors;
                }
                
                function setPrivacyPolicy(uint256 _retention, bool _allowRedaction) public;
                function authorizeRedactor(address _redactor) public;
                function checkRedactionPermission(address _requester) public view returns (bool);
            }
            """,
            is_redactable=True,
            redaction_policies=[
                RedactionPolicy(
                    policy_id="PRIVACY_EXPIRED",
                    policy_type="DELETE",
                    conditions={"retention_expired": True},
                    authorized_roles=["ADMIN", "REGULATOR"],
                    min_approvals=2
                )
            ]
        )
