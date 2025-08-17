import random

class InputsConfig:
    """
    Configuration for smart contract and permissioned blockchain testing.
    This configuration supports both standard and enhanced testing modes.
    
    Use InputsConfig.initialize(testing_mode=True) to enable faster testing configurations.
    
    Select the model to be simulated:
    0 : The base model
    1 : Bitcoin model
    2 : Ethereum model
    
    Usage:
    - Standard mode: InputsConfig.initialize() or InputsConfig.initialize(testing_mode=False)
    - Testing mode: InputsConfig.initialize(testing_mode=True)
    """
    model = 1
    
    # Testing mode - set to True for faster testing with smaller networks
    TESTING_MODE = False
    
    @classmethod
    def initialize(cls, testing_mode=None):
        """Initialize configuration with optional testing mode override"""
        if testing_mode is not None:
            cls.TESTING_MODE = testing_mode
        cls._load_configuration()
    
    @classmethod
    def _load_configuration(cls):
        """Load configuration based on current settings"""
        if cls.model == 1:
            cls._load_bitcoin_config()
    
    @classmethod
    def _load_bitcoin_config(cls):
        """Load Bitcoin model configuration"""
        # Block Parameters
        if cls.TESTING_MODE:
            cls.Binterval = 300  # Faster block creation for testing (5 minutes)
            cls.Bsize = 2.0  # Larger blocks to accommodate smart contracts
        else:
            cls.Binterval = 600  # Average time (in seconds)for creating a block in the blockchain
            cls.Bsize = 1.0  # The block size in MB
        
        cls.Bdelay = 0.42  # average block propogation delay in seconds
        cls.Breward = 12.5  # Reward for mining a block
        
        if cls.TESTING_MODE:
            cls.Rreward = 0.05  # Higher redaction rewards for testing
        else:
            cls.Rreward = 0.03  # Reward for redacting a transaction

        # Transaction Parameters
        cls.hasTrans = True  # True/False to enable/disable transactions in the simulator
        cls.Ttechnique = "Light"  # Full/Light to specify the way of modelling transactions
        
        if cls.TESTING_MODE:
            cls.Tn = 10  # Higher transaction rate for testing
            cls.Tfee = 0.002  # Higher fees for smart contract operations
            cls.Tsize = 0.001  # Larger transaction size for smart contracts
        else:
            cls.Tn = 5  # The rate of the number of transactions to be created per second
            cls.Tfee = 0.001  # The average transaction fee
            cls.Tsize = 0.0006  # The average transaction size in MB

        cls.Tdelay = 5.1 # The average transaction propagation delay in seconds

        # Node Parameters
        if cls.TESTING_MODE:
            cls.NUM_NODES = 50  # Smaller network for faster testing
            cls.MINERS_PORTION = 0.4  # Higher miner percentage for testing
            cls.MAX_HASH_POWER = 100
        else:
            cls.NUM_NODES = 1000  # the total number of nodes in the network
            cls.MINERS_PORTION = 0.3 # Example: 0.5 ==> 50% of miners
            cls.MAX_HASH_POWER = 200
        
        cls.NODES = []
        from Models.Bitcoin.Node import Node
        num_miners = int(cls.NUM_NODES * cls.MINERS_PORTION)

        # Create miners
        for i in range(num_miners):
            if cls.TESTING_MODE:
                hash_power = random.randint(50, cls.MAX_HASH_POWER)  # Higher minimum for testing
            else:
                hash_power = random.randint(1, cls.MAX_HASH_POWER)
            cls.NODES.append(Node(id=i, hashPower=hash_power))
        # Create regular nodes
        for i in range(num_miners, cls.NUM_NODES):
            cls.NODES.append(Node(id=i, hashPower=0))

        # Simulation Parameters
        if cls.TESTING_MODE:
            cls.simTime = 10000  # Shorter simulation for testing
            cls.redactRuns = 5  # More redaction operations for testing
            cls.adminNode = 0  # First node is admin for testing
        else:
            cls.simTime = 100000  # the simulation length (in seconds)
            cls.redactRuns = 1
            cls.adminNode = random.randint(0, len(cls.NODES))
        
        cls.Runs = 1  # Number of simulation runs

        # Redaction Parameters
        cls.hasRedact = True
        cls.hasMulti = True
        
        # Smart Contract Parameters
        cls.hasSmartContracts = True  # Enable smart contract functionality
        cls.DEPLOYED_CONTRACTS = []  # List of deployed contract addresses
        
        if cls.TESTING_MODE:
            cls.contractDeploymentRate = 0.1  # Higher deployment rate for testing
            cls.maxContractsPerBlock = 2
        else:
            cls.contractDeploymentRate = 0.05  # Rate of contract deployment per block
        
        # Permission Parameters
        cls.hasPermissions = True  # Enable permissioned blockchain features
        cls.PERMISSION_LEVELS = {
            "ADMIN": 100,
            "REGULATOR": 80, 
            "MINER": 60,
            "USER": 40,
            "OBSERVER": 20
        }
        
        # Assign roles to nodes
        cls.NODE_ROLES = {}
        
        if cls.TESTING_MODE:
            # Improved role assignment for testing
            num_admins = max(1, cls.NUM_NODES // 10)  # 10% admins
            num_regulators = max(1, cls.NUM_NODES // 10)  # 10% regulators
        else:
            # Standard role assignment
            num_admins = max(1, len(cls.NODES) // 100) if len(cls.NODES) > 0 else 1
            num_regulators = max(1, len(cls.NODES) // 50) if len(cls.NODES) > 0 else 1
        
        # Simple role assignment without complex dependencies
        admin_count = 0
        regulator_count = 0
        
        for i, node in enumerate(cls.NODES):
            if admin_count < num_admins:
                cls.NODE_ROLES[i] = "ADMIN"
                admin_count += 1
            elif regulator_count < num_regulators:
                cls.NODE_ROLES[i] = "REGULATOR"
                regulator_count += 1
            elif node.hashPower > 0:
                cls.NODE_ROLES[i] = "MINER"
            else:
                cls.NODE_ROLES[i] = random.choice(["USER", "OBSERVER"])
        
        # Privacy and Compliance Parameters
        cls.hasPrivacyLevels = True
        if cls.TESTING_MODE:
            cls.dataRetentionPeriod = 86400 * 7  # 1 week for testing
            cls.redactionTimeLimit = 3600  # 1 hour for testing
        else:
            cls.dataRetentionPeriod = 86400 * 365  # 1 year in seconds
        
        cls.requireRedactionApproval = True
        cls.minRedactionApprovals = 2  # Minimum approvals for redaction
        
        # Smart Contract Redaction Policies
        if cls.TESTING_MODE:
            # Enhanced policies for testing
            cls.REDACTION_POLICIES = [
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
        else:
            # Standard policies for production
            cls.REDACTION_POLICIES = [
                {
                    "policy_id": "GDPR_COMPLIANCE",
                    "policy_type": "DELETE",
                    "conditions": {"privacy_request": True, "data_expired": True},
                    "authorized_roles": ["ADMIN", "REGULATOR"],
                    "min_approvals": 2,
                    "time_lock": 86400  # 24 hours
                },
                {
                    "policy_id": "FINANCIAL_AUDIT",
                    "policy_type": "ANONYMIZE", 
                    "conditions": {"audit_required": True},
                    "authorized_roles": ["ADMIN", "REGULATOR"],
                    "min_approvals": 3,
                    "time_lock": 86400 * 7  # 7 days
                },
                {
                    "policy_id": "SECURITY_INCIDENT",
                    "policy_type": "MODIFY",
                    "conditions": {"security_breach": True},
                    "authorized_roles": ["ADMIN"],
                    "min_approvals": 1,
                    "time_lock": 0  # Immediate
                }
            ]
        
        # Testing and Enhanced Features
        # Testing-specific parameters
        cls.ENABLE_DETAILED_LOGGING = cls.TESTING_MODE
        cls.ENABLE_PERFORMANCE_MONITORING = cls.TESTING_MODE
        cls.ENABLE_POLICY_TESTING = cls.TESTING_MODE
        
        # Smart contract testing parameters
        cls.TEST_CONTRACT_TYPES = [
            "AUDIT_CONTRACT",
            "PRIVACY_CONTRACT", 
            "DATA_MANAGEMENT_CONTRACT",
            "IDENTITY_VERIFICATION_CONTRACT",
            "COMPLIANCE_MONITORING_CONTRACT"
        ]
        
        # Transaction mix for testing/simulation
        if cls.TESTING_MODE:
            cls.TRANSACTION_TYPE_DISTRIBUTION = {
                "TRANSFER": 0.60,           # 60% regular transfers
                "CONTRACT_CALL": 0.20,      # 20% smart contract calls
                "CONTRACT_DEPLOY": 0.10,    # 10% contract deployments
                "REDACTION_REQUEST": 0.10   # 10% redaction requests
            }
        else:
            cls.TRANSACTION_TYPE_DISTRIBUTION = {
                "TRANSFER": 0.80,           # 80% regular transfers
                "CONTRACT_CALL": 0.15,      # 15% smart contract calls
                "CONTRACT_DEPLOY": 0.03,    # 3% contract deployments
                "REDACTION_REQUEST": 0.02   # 2% redaction requests
            }
        
        # Privacy level distribution
        if cls.TESTING_MODE:
            cls.PRIVACY_LEVEL_DISTRIBUTION = {
                "PUBLIC": 0.50,        # 50% public transactions
                "PRIVATE": 0.30,       # 30% private transactions
                "CONFIDENTIAL": 0.20   # 20% confidential transactions
            }
        else:
            cls.PRIVACY_LEVEL_DISTRIBUTION = {
                "PUBLIC": 0.70,        # 70% public transactions
                "PRIVATE": 0.25,       # 25% private transactions
                "CONFIDENTIAL": 0.05   # 5% confidential transactions
            }
        
        # Print configuration summary if in testing mode
        if cls.TESTING_MODE:
            print(f"Enhanced Configuration Loaded (Testing Mode):")
            print(f"  Nodes: {cls.NUM_NODES} ({num_miners} miners, {cls.NUM_NODES - num_miners} regular)")
            print(f"  Roles: {num_admins} admins, {num_regulators} regulators")
            print(f"  Smart Contracts: {'Enabled' if cls.hasSmartContracts else 'Disabled'}")
            print(f"  Permissions: {'Enabled' if cls.hasPermissions else 'Disabled'}")
            print(f"  Redaction Policies: {len(cls.REDACTION_POLICIES)} defined")
            print(f"  Simulation Time: {cls.simTime} seconds")
            print(f"  Block Interval: {cls.Binterval} seconds")

# Initialize with default settings
InputsConfig.initialize()

