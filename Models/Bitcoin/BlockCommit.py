import hashlib
import json
import random
import time
import CH.ChameleonHash as ch
import CH.SecretSharing as ss

from CH.ChameleonHash import q, g, SK, PK, KeyGen, forge, chameleonHash
from InputsConfig import InputsConfig as p
from Models.Bitcoin.Consensus import Consensus as c
from Models.BlockCommit import BlockCommit as BaseBlockCommit
from Models.Network import Network
from Models.Transaction import LightTransaction as LT, FullTransaction as FT
from Models.SmartContract import ContractExecutionEngine, PermissionManager
from Scheduler import Scheduler
from Statistics import Statistics

SKlist = []
PKlist = []
shares = []
rlist = []

# Global instances for smart contract and permission management
contract_engine = ContractExecutionEngine()
permission_manager = PermissionManager()

class BlockCommit(BaseBlockCommit):
    # Handling and running Events
    def handle_event(event):
        if event.type == "create_block":
            BlockCommit.generate_block(event)
        elif event.type == "receive_block":
            BlockCommit.receive_block(event)

    # Block Creation Event
    def generate_block(event):
        miner = p.NODES[event.block.miner]
        minerId = miner.id
        eventTime = event.time
        blockPrev = event.block.previous
        if blockPrev == miner.last_block().id:
            Statistics.totalBlocks += 1  # count # of total blocks created!

            if p.hasTrans:
                if p.Ttechnique == "Light":
                    blockTrans, blockSize = LT.execute_transactions()  #Get the created block (transactions and block size)
                    Statistics.blocksSize =blockSize
                elif p.Ttechnique == "Full":
                    blockTrans, blockSize = FT.execute_transactions(miner, eventTime)

                event.block.transactions = blockTrans
                event.block.size = blockSize
                event.block.usedgas = blockSize
                
                # Process smart contract transactions
                if hasattr(p, 'hasSmartContracts') and p.hasSmartContracts:
                    BlockCommit.process_smart_contracts(event.block, miner, eventTime)
                
                # Process redaction requests
                if p.hasRedact and hasattr(p, 'hasPermissions') and p.hasPermissions:
                    BlockCommit.process_redaction_requests(event.block, miner, eventTime)

                # hash the transactions and previous hash value
                if p.hasRedact:
                    event.block.r = random.randint(1, q)
                    x = json.dumps([[i.id for i in event.block.transactions], event.block.previous],
                                   sort_keys=True).encode()
                    m = hashlib.sha256(x).hexdigest()
                    event.block.id = chameleonHash(miner.PK, m, event.block.r)
                    
                    # Store original hash for redaction tracking
                    event.block.original_hash = event.block.id
            
            miner.blockchain.append(event.block)

            if p.hasTrans and p.Ttechnique == "Light":
                LT.create_transactions()  # generate transactions

            BlockCommit.propagate_block(event.block)
            BlockCommit.generate_next_block(miner, eventTime)  # Start mining or working on the next block

    # Block Receiving Event
    def receive_block(event):
        miner = p.NODES[event.block.miner]
        minerId = miner.id
        currentTime = event.time
        blockPrev = event.block.previous  # previous block id
        node = p.NODES[event.node]  # recipient
        lastBlockId = node.last_block().id  # the id of last block

        #### case 1: the received block is built on top of the last block according to the recipient's blockchain ####
        if blockPrev == lastBlockId:
            node.blockchain.append(event.block)  # append the block to local blockchain
            if p.hasTrans and p.Ttechnique == "Full":
                BlockCommit.update_transactionsPool(node, event.block)
            BlockCommit.generate_next_block(node, currentTime)  # Start mining or working on the next block

        #### case 2: the received block is not built on top of the last block ####
        else:
            depth = event.block.depth + 1
            if depth > len(node.blockchain):
                BlockCommit.update_local_blockchain(node, miner, depth)
                BlockCommit.generate_next_block(node, currentTime)  # Start mining or working on the next block

            if p.hasTrans and p.Ttechnique == "Full":
                BlockCommit.update_transactionsPool(node, event.block)  # not sure yet.


    # Upon generating or receiving a block, the miner start working on the next block as in POW
    def generate_next_block(node, currentTime):
        if node.hashPower > 0:
            blockTime = currentTime + c.Protocol(node)  # time when miner x generate the next block
            Scheduler.create_block_event(node, blockTime)

    def generate_initial_events():
        currentTime = 0
        for node in p.NODES:
            BlockCommit.generate_next_block(node, currentTime)

    def propagate_block(block):
        for recipient in p.NODES:
            if recipient.id != block.miner:
                blockDelay = Network.block_prop_delay()
                # draw block propagation delay from a distribution !! or assign 0 to ignore block propagation delay
                Scheduler.receive_block_event(recipient, block, blockDelay)

    def setupSecretSharing():
        global SKlist, PKlist, rlist, shares
        SKlist, PKlist = KeyGen(ch.p, q, g, len(p.NODES))
        rlist = ch.getr(len(p.NODES), q)
        for i, node in enumerate(p.NODES):
            node.PK = PKlist[i]
            node.SK = SKlist[i]

    def generate_redaction_event(redactRuns):
        t1 = time.time()
        i = 0
        miner_list = [node for node in p.NODES if node.hashPower > 0]
        while i < redactRuns:
            if p.hasMulti:
                miner = random.choice(miner_list)
            else:
                miner = p.NODES[p.adminNode]
            r = random.randint(1, 2)
            # r =2
            block_index = random.randint(1, len(miner.blockchain)-1)
            tx_index = random.randint(1, len(miner.blockchain[block_index].transactions)-1)
            if r == 1:
                BlockCommit.redact_tx(miner, block_index, tx_index, p.Tfee)
            else:
                BlockCommit.delete_tx(miner, block_index, tx_index)
            t2=time.time()
            t = (t2 - t1) * 1000  # in ms
            print(f"Redaction time = {t} ms")
            i += 1

    def delete_tx(miner, i, tx_i):
        t1 = time.time()
        block = miner.blockchain[i]
        # Store the old block data
        x1 = json.dumps([[i.id for i in block.transactions], block.previous], sort_keys=True).encode()
        m1 = hashlib.sha256(x1).hexdigest()

        # record the block index and deleted transaction object, miner reward  = 0 and performance time = 0
        # and also the blockchain size, number of transaction of that action block
        miner.redacted_tx.append([i, block.transactions.pop(tx_i), 0, 0, miner.blockchain_length(), len(block.transactions)])

        # Store the modified block data
        x2 = json.dumps([[i.id for i in block.transactions], block.previous], sort_keys=True).encode()
        m2 = hashlib.sha256(x2).hexdigest()
        # Forge new r
        # t1 = time.time()
        if p.hasMulti:
            # rlist = block.r
            miner_list = [miner for miner in p.NODES if miner.hashPower > 0]
            # propagation delay in sharing secret key
            # time.sleep(0.005)
            # SKlist[miner.id] = ss.secret_share(SKlist[miner.id], minimum=len(miner_list), shares=len(p.NODES))
            # r2 = forgeSplit(SKlist, m1, rlist, m2, q, miner.id)
            # rlist[miner.id] = r2
            ss.secret_share(SK, minimum=len(miner_list), shares=len(p.NODES))
            r2 = forge(SK, m1, block.r, m2)
            # print(f'rlist_temp: {rlist}')
            id2 = chameleonHash(PK, m2, r2)
            # print(f'block new id: {id2}')
            block.r = r2
            for node in p.NODES:
                if node.id != miner.id:
                    if node.blockchain[i]:
                        node.blockchain[i].transactions = block.transactions
                        node.blockchain[i].r = block.r
        else:
            r2 = forge(SK, m1, block.r, m2)
            id2 = chameleonHash(PK, m2, r2)

            block.r = r2
        t2 = time.time()
        block.id = id2
        # Calculate the performance time per operation
        # t2 = time.time()
        t = (t2 - t1) * 1000 # in ms
        # redact operation is more expensive than mining
        # print(f"Redaction succeeded in {t}")
        reward = random.expovariate(1 / p.Rreward)
        miner.balance += reward
        miner.redacted_tx[-1][2] = reward
        miner.redacted_tx[-1][3] = t
        return miner

    def redact_tx(miner, i, tx_i, fee):
        t1 = time.time()
        block = miner.blockchain[i]
        # Store the old block data
        x1 = json.dumps([[i.id for i in block.transactions], block.previous], sort_keys=True).encode()
        m1 = hashlib.sha256(x1).hexdigest()

        # record the block depth and modify transaction information then recompute the transaction id
        block.transactions[tx_i].fee = fee
        block.transactions[tx_i].id = random.randrange(100000000000)
        # record the block depth, redacted transaction, miner reward = 0 and performance time = 0
        miner.redacted_tx.append([i, block.transactions[tx_i], 0, 0, miner.blockchain_length(), len(block.transactions)])
        # Store the modified block data
        x2 = json.dumps([[i.id for i in block.transactions], block.previous], sort_keys=True).encode()
        m2 = hashlib.sha256(x2).hexdigest()
        # Forge new r
        # t1 = time.time()
        if p.hasMulti:
            # here I am sending the secret key i to the performing miner
            miner_list = [miner for miner in p.NODES if miner.hashPower > 0]
            # propagation delay in sharing secret key
            time.sleep(0.005)
            ss.secret_share(SK, minimum=len(miner_list), shares=len(p.NODES))
            r2 = forge(SK, m1, block.r, m2)
            # compute new block id and update randomness
            id2 = chameleonHash(PK, m2, r2)
            block.r = r2
            for node in p.NODES:
                if node.id != miner.id:
                    if node.blockchain[i]:
                        node.blockchain[i].transactions = block.transactions
                        node.blockchain[i].r = block.r
        else:
            r2 = forge(SK, m1, block.r, m2)
            id2 = chameleonHash(PK, m2, r2)
            block.r = r2
        t2 = time.time()
        block.id = id2
        # Calculate the performance time per operation
        t = (t2 - t1) * 1000 # in ms
        # print(f"Redaction succeeded in {t}")
        # redact operation is more expensive than mining
        reward = random.expovariate(1 / p.Rreward)
        miner.balance += reward
        miner.redacted_tx[-1][2] = reward
        miner.redacted_tx[-1][3] = t
        return miner
    
    @staticmethod
    def process_smart_contracts(block, miner, event_time):
        """Process smart contract transactions in the block."""
        from Models.SmartContract import SmartContract, ContractCall
        
        for tx in block.transactions:
            if hasattr(tx, 'tx_type') and tx.tx_type == "CONTRACT_CALL" and tx.contract_call:
                # Execute the smart contract call
                success = contract_engine.execute_call(tx.contract_call, event_time)
                if success:
                    block.contract_calls.append(tx.contract_call)
                    
            elif hasattr(tx, 'tx_type') and tx.tx_type == "CONTRACT_DEPLOY":
                # Deploy a new smart contract
                if miner.can_perform_action("DEPLOY"):
                    contract_address = miner.deploy_contract(
                        f"contract_code_{tx.id}", 
                        "GENERAL"
                    )
                    if contract_address:
                        p.DEPLOYED_CONTRACTS.append(contract_address)
                        block.smart_contracts.append(contract_address)
    
    @staticmethod
    def process_redaction_requests(block, miner, event_time):
        """Process redaction requests in the block."""
        redaction_requests = []
        
        for tx in block.transactions:
            if hasattr(tx, 'tx_type') and tx.tx_type == "REDACTION_REQUEST":
                if miner.can_perform_action("REDACT"):
                    request_id = miner.request_redaction(
                        tx.metadata.get("target_block", 0),
                        tx.metadata.get("target_tx", 0),
                        tx.metadata.get("redaction_type", "DELETE"),
                        tx.metadata.get("reason", "No reason provided")
                    )
                    if request_id:
                        redaction_requests.append(request_id)
        
        # Process pending redaction votes
        BlockCommit.process_redaction_voting(block, miner, event_time)
        
        return redaction_requests
    
    @staticmethod
    def process_redaction_voting(block, miner, event_time):
        """Process voting on pending redaction requests."""
        # Check for pending redaction requests that need votes
        for node in p.NODES:
            for request in node.redaction_requests:
                if request["status"] == "PENDING":
                    # Simulate voting by other authorized nodes
                    BlockCommit.simulate_redaction_voting(request, block, event_time)
    
    @staticmethod
    def simulate_redaction_voting(request, block, event_time):
        """Simulate voting process for redaction requests."""
        if not hasattr(p, 'NODE_ROLES'):
            return # No roles defined, skip voting
        
        authorized_voters = [
            node for node in p.NODES 
            if p.NODE_ROLES.get(node.id, "USER") in ["ADMIN", "REGULATOR"]
        ]
        
        votes_needed = getattr(p, 'minRedactionApprovals', 2)
        votes_received = request.get("approvals", 0)
        
        # Simulate voting with 70% approval rate
        rv = random.randint(votes_needed, len(authorized_voters)-1)  # random number of voters between the quorum (votes_needed) and the total of authorized voters

        for voter in authorized_voters[:rv]:
            if voter.id not in [r["voter"] for r in voter.redaction_approvals if r["request_id"] == request["request_id"]]:
                vote = random.random() < 0.7  # 70% approval rate
                if voter.vote_on_redaction(request["request_id"], vote, "Automated vote"):
                    if vote:
                        request["approvals"] += 1
        
        # Check if redaction is approved
        if request["approvals"] >= votes_needed:
            request["status"] = "APPROVED"
            BlockCommit.execute_approved_redaction(request, block, event_time)
        elif len(authorized_voters) - request["approvals"] < votes_needed:  # if there aren't enough votes left to reach the quorum, mark as rejected in order to save the next voting simulation
            request["status"] = "REJECTED"
        # else: the request remains "pending"
    
    @staticmethod
    def execute_approved_redaction(request, block, event_time):
        """Execute an approved redaction request."""
        target_block = request["target_block"]
        target_tx = request["target_tx"]
        redaction_type = request["redaction_type"]
        requester_id = request["requester"]
        
        # Find the requester node
        requester = next((node for node in p.NODES if node.id == requester_id), None)  # next() is used to find the first matching node inside the generator
        if not requester or target_block >= len(requester.blockchain):  # if target_block is out of range
            return False
        
        target_block_obj = requester.blockchain[target_block]
        if target_tx >= len(target_block_obj.transactions):
            return False
        
        # Record the redaction
        approvers = [
            approval["voter"] for approval in requester.redaction_approvals 
            if approval["request_id"] == request["request_id"] and approval["vote"]
        ]
        target_block_obj.add_redaction_record(
            redaction_type, target_tx, requester_id, approvers
        )
        
        # Perform the actual redaction
        if redaction_type == "DELETE":
            BlockCommit.delete_tx(requester, target_block, target_tx)
        elif redaction_type == "MODIFY":
            # Modify transaction to anonymize sensitive data
            target_tx_obj = target_block_obj.transactions[target_tx]
            target_tx_obj.value = "REDACTED"
            target_tx_obj.metadata = {"redacted": True, "original_redacted": True}
            BlockCommit.redact_tx(requester, target_block, target_tx, 0.001)
        elif redaction_type == "ANONYMIZE":
            # Anonymize transaction data
            target_tx_obj = target_block_obj.transactions[target_tx]
            target_tx_obj.sender = 0
            target_tx_obj.to = 0
            target_tx_obj.metadata = {"anonymized": True}
            BlockCommit.redact_tx(requester, target_block, target_tx, 0.001)
        
        return True
    
    @staticmethod
    def check_redaction_policy(redaction_type, requester_role):
        """Check if a redaction request complies with the defined policies."""
        if not hasattr(p, 'REDACTION_POLICIES'):
            return True  # No policies defined, allow all
        
        for policy in p.REDACTION_POLICIES:
            if policy["policy_type"] == redaction_type:
                if requester_role in policy["authorized_roles"]:
                    # Additional condition checks could be added here
                    return True
        
        return False
