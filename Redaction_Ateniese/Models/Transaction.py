import random
from InputsConfig import InputsConfig as p
import Models.Network as Network
import operator
import copy
from Models.SmartContract import ContractCall


class Transaction(object):
    """ Defines the Improved Transaction model for Smart Contract support.

    :param int id: the uinque id or the hash of the transaction
    :param int timestamp: the time when the transaction is created. In case of Full technique, this will be array of two value (transaction creation time and receiving time)
    :param int sender: the id of the node that created and sent the transaction
    :param int to: the id of the recipint node
    :param int value: the amount of cryptocurrencies to be sent to the recipint node
    :param int size: the transaction size in MB
    :param int gasLimit: the maximum amount of gas units the transaction can use. It is specified by the submitter of the transaction
    :param int usedGas: the amount of gas used by the transaction after its execution on the EVM
    :param int gasPrice: the amount of cryptocurrencies (in Gwei) the submitter of the transaction is willing to pay per gas unit
    :param float fee: the fee of the transaction (usedGas * gasPrice)
    :param str tx_type: type of transaction (TRANSFER, CONTRACT_CALL, CONTRACT_DEPLOY, REDACTION_REQUEST)
    :param ContractCall contract_call: smart contract call data (if applicable)
    :param dict metadata: additional metadata for the transaction
    :param bool is_redactable: whether this transaction can be redacted
    :param str privacy_level: privacy level (PUBLIC, PRIVATE, CONFIDENTIAL)
    """

    def __init__(self,
                 id=0,
                 timestamp=0 or [],
                 sender=0,
                 to=0,
                 value=0,
                 size=0.000546,
                 fee=0,
                 tx_type="TRANSFER", # TRANSFER, CONTRACT_CALL, CONTRACT_DEPLOY, REDACTION_REQUEST
                 contract_call=None,
                 metadata=None,
                 is_redactable=True,
                 privacy_level="PUBLIC"):
        self.id = id
        self.timestamp = timestamp
        self.sender = sender
        self.to = to
        self.value = value
        self.size = size
        self.fee = fee
        self.tx_type = tx_type
        self.contract_call = contract_call
        self.metadata = metadata or {}
        self.is_redactable = is_redactable
        self.privacy_level = privacy_level


class LightTransaction():
    pending_transactions = []  # shared pool of pending transactions

    def create_transactions():
        LightTransaction.pending_transactions = []
        pool = LightTransaction.pending_transactions
        Psize = int(p.Tn * p.Binterval)  # (The nbr of tx to be created per s / time (in s) creating a block)
        Bsize = 0  # block size in MB
        for i in range(Psize):
            # assign values for transactions' attributes. You can ignore some attributes if not of an interest, and the default values will then be used
            tx = Transaction()
            tx.id = random.randrange(100000000000)
            tx.sender = random.choice(p.NODES).id
            tx.to = random.choice(p.NODES).id
            tx.size = random.expovariate(1 / p.Tsize)
            tx.fee = random.expovariate(1 / p.Tfee)
            
            # Determine transaction type based on probability  # TODO make this a function to be reused in FullTransaction
            rand_val = random.random()
            if rand_val < 0.1 and hasattr(p, 'hasSmartContracts') and p.hasSmartContracts:  # 10% smart contract calls
                tx.tx_type = "CONTRACT_CALL"
                tx.contract_call = ContractCall(
                    contract_address=random.choice(p.DEPLOYED_CONTRACTS) if hasattr(p, 'DEPLOYED_CONTRACTS') and p.DEPLOYED_CONTRACTS else "",
                    function_name=random.choice(["transfer", "approve", "mint", "burn", "getData"]),
                    parameters=[random.randint(1, 1000), random.randint(1, 100)],
                    caller=str(tx.sender),
                    gas_limit=random.randint(50000, 200000)
                )
                tx.size *= 1.5  # Smart contract calls are larger
            elif rand_val < 0.15 and hasattr(p, 'hasSmartContracts') and p.hasSmartContracts:  # 5% contract deployment (15% - 10% = 5%)
                tx.tx_type = "CONTRACT_DEPLOY"
                tx.size *= 3  # Contract deployment is much larger
                tx.fee *= 2  # Higher fee for deployment
            elif rand_val < 0.2 and p.hasRedact:  # 5% redaction requests (20% - 15% = 5%)
                tx.tx_type = "REDACTION_REQUEST"
                tx.metadata = {
                    "target_block": random.randint(1, 10),
                    "target_tx": random.randint(0, 5),
                    "redaction_type": random.choice(["DELETE", "MODIFY", "ANONYMIZE"]),
                    "reason": "Privacy compliance"
                }
            else:  # 80% regular transfers (100% - 20% = 80%)
                tx.tx_type = "TRANSFER"
            
            # Set privacy level  # TODO make this a function to be reused in FullTransaction
            privacy_rand = random.random()
            if privacy_rand < 0.7:
                tx.privacy_level = "PUBLIC"
            elif privacy_rand < 0.9:
                tx.privacy_level = "PRIVATE"
            else:
                tx.privacy_level = "CONFIDENTIAL"
                tx.is_redactable = True  # Confidential transactions are always redactable
            
            pool += [tx]  # add to pending transactions pool
            Bsize += tx.size
        random.shuffle(pool)

    ##### Select and execute a number of transactions to be added in the next block #####
    def execute_transactions():
        transactions = []  # prepare a list of transactions to be included in the block
        size = 0  # calculate the total block gaslimit
        count = 0
        blocksize = p.Bsize

        pool = LightTransaction.pending_transactions

        pool = sorted(pool, key=lambda x: x.fee,
                      reverse=True)  # sort pending transactions in the pool based on the gasPrice value

        while count < len(pool):
            if blocksize >= pool[count].size:
                blocksize -= pool[count].size
                transactions += [pool[count]]
                size += pool[count].size
            count += 1
        # print('Block of Size ===== '+str(size)+' has been created. It contains ====== '+str(len(transactions))+'transactions')
        return transactions, size


class FullTransaction():

    def create_transactions():
        Psize = int(p.Tn * p.simTime)

        for i in range(Psize):
            # assign values for transactions' attributes. You can ignore some attributes if not of an interest, and the default values will then be used
            tx = Transaction()

            tx.id = random.randrange(100000000000)
            creation_time = random.randint(0, p.simTime - 1)
            receive_time = creation_time
            tx.timestamp = [creation_time, receive_time]
            sender = random.choice(p.NODES)
            tx.sender = sender.id
            tx.to = random.choice(p.NODES).id
            tx.size = random.expovariate(1 / p.Tsize)
            tx.fee = random.expovariate(1 / p.Tfee)
            
            # Improved transaction types for smart contracts
            rand_val = random.random()
            if rand_val < 0.1 and hasattr(p, 'hasSmartContracts') and p.hasSmartContracts:
                tx.tx_type = "CONTRACT_CALL"
                tx.contract_call = ContractCall(
                    contract_address=random.choice(p.DEPLOYED_CONTRACTS) if hasattr(p, 'DEPLOYED_CONTRACTS') and p.DEPLOYED_CONTRACTS else "",
                    function_name=random.choice(["transfer", "approve", "mint", "burn", "getData"]),
                    parameters=[random.randint(1, 1000), random.randint(1, 100)],
                    caller=str(tx.sender),
                    gas_limit=random.randint(50000, 200000)
                )
                tx.size *= 1.5
            elif rand_val < 0.15 and hasattr(p, 'hasSmartContracts') and p.hasSmartContracts:
                tx.tx_type = "CONTRACT_DEPLOY"
                tx.size *= 3
                tx.fee *= 2
            elif rand_val < 0.2 and p.hasRedact:
                tx.tx_type = "REDACTION_REQUEST"
                tx.metadata = {
                    "target_block": random.randint(1, 10),
                    "target_tx": random.randint(0, 5),
                    "redaction_type": random.choice(["DELETE", "MODIFY", "ANONYMIZE"]),
                    "reason": "Privacy compliance"
                }
            else:
                tx.tx_type = "TRANSFER"
            
            # Set privacy level
            privacy_rand = random.random()
            if privacy_rand < 0.7:
                tx.privacy_level = "PUBLIC"
            elif privacy_rand < 0.9:
                tx.privacy_level = "PRIVATE"
            else:
                tx.privacy_level = "CONFIDENTIAL"
                tx.is_redactable = True

            sender.transactionsPool.append(tx)
            FullTransaction.transaction_prop(tx)  # propogate transaction to other nodes

    # Transaction propogation & preparing pending lists for miners
    def transaction_prop(tx):
        # Fill each pending list. This is for transaction propagation
        for i in p.NODES:
            if tx.sender != i.id:
                t = copy.deepcopy(tx)
                t.timestamp[1] = t.timestamp[1] + Network.tx_prop_delay()  # transaction propogation delay in seconds
                i.transactionsPool.append(t)

    def execute_transactions(miner, currentTime):
        transactions = []  # prepare a list of transactions to be included in the block
        size = 0  # calculate the total block gaslimit
        count = 0
        blocksize = p.Bsize
        miner.transactionsPool.sort(key=operator.attrgetter('fee'), reverse=True)
        pool = miner.transactionsPool

        while count < len(pool):
            if blocksize >= pool[count].size and pool[count].timestamp[1] <= currentTime:
                blocksize -= pool[count].size
                transactions += [pool[count]]
                size += pool[count].size
            count += 1

        return transactions, size
