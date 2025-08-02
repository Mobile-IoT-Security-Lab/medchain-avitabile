import time

class Block(object):
    """ Defines the improved Block model with smart contract support.

    :param int depth: the index of the block in the local blockchain ledger (0 for genesis block)
    :param int id: the uinque id or the hash of the block
    :param int previous: the uinque id or the hash of the previous block
    :param int timestamp: the time when the block is created
    :param int miner: the id of the miner who created the block
    :param list transactions: a list of transactions included in the block
    :param int size: the block size in MB
    :param int r: the randomness value to implement chameleon hash function
    :param list smart_contracts: list of smart contracts deployed in this block
    :param list contract_calls: list of smart contract calls executed in this block
    :param dict redaction_metadata: metadata about redactions performed on this block
    :param str block_type: type of block (NORMAL, GENESIS, REDACTION)
    :param dict privacy_data: privacy-related data and settings
    """

    def __init__(self,
                 depth=0,
                 id=0,
                 previous=-1,
                 timestamp=0,
                 miner=None,
                 transactions=[],
                 size=1.0,
                 r=0,
                 smart_contracts=None,
                 contract_calls=None,
                 redaction_metadata=None,
                 block_type="NORMAL",
                 privacy_data=None
                 ):
        self.depth = depth
        self.id = id
        self.previous = previous
        self.timestamp = timestamp
        self.miner = miner
        self.transactions = transactions or []
        self.size = size
        self.r = r  # Randomness for chameleon hash
        self.smart_contracts = smart_contracts or []
        self.contract_calls = contract_calls or []
        self.redaction_metadata = redaction_metadata or {}
        self.block_type = block_type
        self.privacy_data = privacy_data or {}
        
        # Redaction tracking
        self.original_hash = None  # Hash before any redaction
        self.redaction_history = []  # List of redactions performed
        self.redaction_approvals = []  # List of approvals for redactions
        
    def add_redaction_record(self, redaction_type: str, target_tx: int, requester: int, approvers: list):
        """Add a record of redaction performed on this block."""
        redaction_record = {
            "timestamp": time.time(),
            "type": redaction_type,
            "target_transaction": target_tx,
            "requester": requester,
            "approvers": approvers,
            "block_hash_before": self.original_hash,
            "block_hash_after": self.id
        }
        self.redaction_history.append(redaction_record)
    
    def is_redactable(self) -> bool:
        """Check if this block can be redacted."""
        # Genesis blocks and audit blocks should not be redactable
        if self.depth == 0 or self.block_type == "AUDIT":
            return False
        
        # Check if any transactions in the block are non-redactable
        for tx in self.transactions:
            if hasattr(tx, 'is_redactable') and not tx.is_redactable:
                return False
        
        return True
    
    def get_smart_contract_state(self) -> dict:
        """Get the state of all smart contracts in this block."""
        contract_states = {}
        for contract in self.smart_contracts:
            if hasattr(contract, 'state'):
                contract_states[contract.address] = contract.state
        return contract_states
