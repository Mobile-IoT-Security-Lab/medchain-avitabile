from Models.Block import Block
from Models.Node import Node as BaseNode
from Models.SmartContract import PermissionManager, ContractExecutionEngine
from CH.ChameleonHash import PK, SK, p, q, g
import time
import uuid


class Node(BaseNode):
    def __init__(self, id, hashPower):
        '''Initialize a new enhanced node with smart contract and permission support.'''
        super().__init__(id)  # ,blockchain,transactionsPool,blocks,balance)
        self.hashPower = hashPower
        self.blockchain = []  # create an array for each miner to store chain state locally
        self.transactionsPool = []
        self.blocks = 0  # total number of blocks mined in the main chain
        self.balance = 0  # to count all reward that a miner made, including block rewards + transactions fees
        self.PK = PK
        self.SK = SK
        
        # Enhanced features for smart contracts and permissions
        self.role = "USER"  # Default role, will be updated from InputsConfig
        self.permissions = []
        self.deployed_contracts = []  # Contracts deployed by this node
        self.contract_calls = []  # History of contract calls made by this node
        self.redaction_requests = []  # Redaction requests made by this node
        self.redaction_approvals = []  # Redaction approvals given by this node
        self.privacy_settings = {
            "allow_redaction": True,
            "data_retention_period": 86400 * 365,  # 1 year
            "privacy_level": "STANDARD"
        }
        
        # Voting and consensus for redaction
        self.voted_redactions = set()  # Track redactions this node has voted on
        self.redaction_votes = {}  # redaction_id -> vote (True/False)
        
    def update_role(self, role: str):
        """Update the node's role and permissions."""
        self.role = role
        # Update permissions based on role
        from InputsConfig import InputsConfig as p
        if hasattr(p, 'PERMISSION_LEVELS') and role in p.PERMISSION_LEVELS:
            self.permissions = self._get_role_permissions(role)
    
    def _get_role_permissions(self, role: str) -> list:
        """Get permissions for a given role."""
        role_permissions = {
            "ADMIN": ["READ", "WRITE", "DEPLOY", "REDACT", "APPROVE", "AUDIT"],
            "REGULATOR": ["READ", "AUDIT", "REDACT", "APPROVE"],
            "MINER": ["READ", "WRITE", "MINE", "VALIDATE"],
            "USER": ["READ", "WRITE", "TRANSACT"],
            "OBSERVER": ["READ"]
        }
        return role_permissions.get(role, ["READ"])
    
    def can_perform_action(self, action: str) -> bool:
        """Check if the node can perform a specific action."""
        return action in self.permissions or "ALL" in self.permissions
    
    def deploy_contract(self, contract_code: str, contract_type: str = "GENERAL") -> str:
        """Deploy a smart contract from this node."""
        if not self.can_perform_action("DEPLOY"):
            return None
        
        from Models.SmartContract import SmartContract
        import hashlib
        import random
        
        contract = SmartContract(
            address=hashlib.sha256(f"{self.id}{contract_code}{random.random()}".encode()).hexdigest()[:40],
            code=contract_code,
            owner=str(self.id),
            is_redactable=(contract_type != "AUDIT")
        )
        
        self.deployed_contracts.append(contract.address)
        return contract.address
    
    def request_redaction(self, target_block: int, target_tx: int, redaction_type: str, reason: str) -> str:
        """Request redaction of a specific transaction."""
        if not self.can_perform_action("REDACT"):
            return None
        
        request_id = str(uuid.uuid4())
        redaction_request = {
            "request_id": request_id,
            "requester": self.id,
            "target_block": target_block,
            "target_tx": target_tx,
            "redaction_type": redaction_type,
            "reason": reason,
            "timestamp": time.time(),
            "status": "PENDING",
            "approvals": 0,
            "required_approvals": 2  # Default minimum approvals
        }
        
        self.redaction_requests.append(redaction_request)
        return request_id
    
    def vote_on_redaction(self, request_id: str, vote: bool, reason: str = "") -> bool:
        """Vote on a redaction request."""
        if not self.can_perform_action("APPROVE"):
            return False
        
        if request_id in self.voted_redactions:
            return False  # Already voted
        
        self.voted_redactions.add(request_id)
        self.redaction_votes[request_id] = vote
        
        approval_record = {
            "request_id": request_id,
            "voter": self.id,
            "vote": vote,
            "reason": reason,
            "timestamp": time.time()
        }
        
        self.redaction_approvals.append(approval_record)
        return True

# print(PK, SK, g)
