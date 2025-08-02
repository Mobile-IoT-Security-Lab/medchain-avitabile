import random

class EnhancedInputsConfig:
    """
    Improved configuration for smart contract and permissioned blockchain testing.
    This configuration is optimized for demonstrating the new features.
    """
    
    # Model selection
    model = 1  # Bitcoin model with enhancements
    
    # Improved Block Parameters
    Binterval = 300  # Faster block creation for testing (5 minutes)
    Bsize = 2.0  # Larger blocks to accommodate smart contracts
    Bdelay = 0.42
    Breward = 12.5
    Rreward = 0.05  # Higher redaction rewards
    
    # Improved Transaction Parameters
    hasTrans = True
    Ttechnique = "Light"
    Tn = 10  # Higher transaction rate for testing
    Tdelay = 5.1
    Tfee = 0.002  # Higher fees for smart contract operations
    Tsize = 0.001  # Larger transaction size for smart contracts
    
    # Improved Node Parameters for Testing
    NUM_NODES = 50  # Smaller network for faster testing
    NODES = []
    MINERS_PORTION = 0.4  # Higher miner percentage
    MAX_HASH_POWER = 100
    
    # Create improved node structure
    from Models.Bitcoin.Node import Node
    num_miners = int(NUM_NODES * MINERS_PORTION)
    
    # Create miners
    for i in range(num_miners):
        hash_power = random.randint(50, MAX_HASH_POWER)
        NODES.append(Node(id=i, hashPower=hash_power))
    
    # Create regular nodes
    for i in range(num_miners, NUM_NODES):
        NODES.append(Node(id=i, hashPower=0))
    
    # Improved Simulation Parameters
    simTime = 10000  # Shorter simulation for testing
    Runs = 1
    
    # Improved Redaction Parameters
    hasRedact = True
    hasMulti = True
    redactRuns = 5  # More redaction operations for testing
    adminNode = 0  # First node is admin
    
    # Smart Contract Parameters (Improved)
    hasSmartContracts = True
    DEPLOYED_CONTRACTS = []
    contractDeploymentRate = 0.1  # Higher deployment rate for testing
    maxContractsPerBlock = 2
    
    # Permission Parameters (Improved)
    hasPermissions = True
    PERMISSION_LEVELS = {
        "ADMIN": 100,
        "REGULATOR": 80,
        "MINER": 60,
        "USER": 40,
        "OBSERVER": 20
    }
    
    # Improved role assignment for testing
    NODE_ROLES = {}
    
    # Assign specific roles for testing
    admin_count = max(1, NUM_NODES // 10)  # 10% admins
    regulator_count = max(1, NUM_NODES // 10)  # 10% regulators
    
    role_assignment_count = 0
    for i, node in enumerate(NODES):
        if role_assignment_count < admin_count:
            NODE_ROLES[i] = "ADMIN"
        elif role_assignment_count < admin_count + regulator_count:
            NODE_ROLES[i] = "REGULATOR"
        elif node.hashPower > 0:
            NODE_ROLES[i] = "MINER"
        else:
            NODE_ROLES[i] = random.choice(["USER", "OBSERVER"])
        role_assignment_count += 1
    
    # Privacy and Compliance Parameters (Improved)
    hasPrivacyLevels = True
    dataRetentionPeriod = 86400 * 7  # 1 week for testing
    requireRedactionApproval = True
    minRedactionApprovals = 2
    redactionTimeLimit = 3600  # 1 hour for testing
    
    # Improved Smart Contract Redaction Policies
    REDACTION_POLICIES = [
        {
            "policy_id": "TEST_GDPR_COMPLIANCE",
            "policy_type": "DELETE",
            "conditions": {"privacy_request": True, "user_consent": True},
            "authorized_roles": ["ADMIN", "REGULATOR"],
            "min_approvals": 2,
            "time_lock": 300  # 5 minutes for testing
        },
        {
            "policy_id": "TEST_AUDIT_REQUIREMENT",
            "policy_type": "ANONYMIZE",
            "conditions": {"audit_required": True},
            "authorized_roles": ["ADMIN", "REGULATOR"],
            "min_approvals": 2,
            "time_lock": 600  # 10 minutes for testing
        },
        {
            "policy_id": "TEST_SECURITY_INCIDENT",
            "policy_type": "MODIFY",
            "conditions": {"security_breach": True, "emergency": True},
            "authorized_roles": ["ADMIN"],
            "min_approvals": 1,
            "time_lock": 0  # Immediate for testing
        },
        {
            "policy_id": "TEST_DATA_CORRECTION",
            "policy_type": "MODIFY",
            "conditions": {"data_error": True},
            "authorized_roles": ["ADMIN", "REGULATOR", "USER"],
            "min_approvals": 3,
            "time_lock": 1800  # 30 minutes for testing
        }
    ]
    
    # Testing-specific parameters
    ENABLE_DETAILED_LOGGING = True
    ENABLE_PERFORMANCE_MONITORING = True
    ENABLE_POLICY_TESTING = True
    
    # Smart contract testing parameters
    TEST_CONTRACT_TYPES = [
        "AUDIT_CONTRACT",
        "PRIVACY_CONTRACT", 
        "DATA_MANAGEMENT_CONTRACT",
        "IDENTITY_VERIFICATION_CONTRACT",
        "COMPLIANCE_MONITORING_CONTRACT"
    ]
    
    # Transaction mix for testing
    TRANSACTION_TYPE_DISTRIBUTION = {
        "TRANSFER": 0.60,           # 60% regular transfers
        "CONTRACT_CALL": 0.20,      # 20% smart contract calls
        "CONTRACT_DEPLOY": 0.10,    # 10% contract deployments
        "REDACTION_REQUEST": 0.10   # 10% redaction requests
    }
    
    # Privacy level distribution for testing
    PRIVACY_LEVEL_DISTRIBUTION = {
        "PUBLIC": 0.50,        # 50% public transactions
        "PRIVATE": 0.30,       # 30% private transactions
        "CONFIDENTIAL": 0.20   # 20% confidential transactions
    }
    
    print(f"Improved Configuration Loaded:")
    print(f"  Nodes: {NUM_NODES} ({num_miners} miners, {NUM_NODES - num_miners} regular)")
    print(f"  Roles: {admin_count} admins, {regulator_count} regulators")
    print(f"  Smart Contracts: {'Enabled' if hasSmartContracts else 'Disabled'}")
    print(f"  Permissions: {'Enabled' if hasPermissions else 'Disabled'}")
    print(f"  Redaction Policies: {len(REDACTION_POLICIES)} defined")
