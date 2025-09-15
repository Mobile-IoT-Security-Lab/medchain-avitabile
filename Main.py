import os
from InputsConfig import InputsConfig as p
from Event import Queue
from Statistics import Statistics
import time
from Models.Bitcoin.BlockCommit import BlockCommit
from Models.Bitcoin.Consensus import Consensus
from Models.Transaction import LightTransaction as LT, FullTransaction as FT
from Models.Bitcoin.Node import Node
from Models.Incentives import Incentives

########################################################## Start Simulation ##############################################################


def main():
    # Optionally re-initialize configuration from environment flag before anything else
    # Usage: TESTING_MODE=1 python Main.py
    env_flag = os.getenv("TESTING_MODE")
    if env_flag is not None:
        is_testing = env_flag.strip().lower() in ("1", "true", "yes", "on")
        try:
            p.initialize(testing_mode=is_testing)
            print(f"Config initialized from TESTING_MODE={env_flag} (testing_mode={is_testing})")
        except Exception as e:
            print(f"Warning: failed to re-initialize config from TESTING_MODE: {e}")
    # Optional DRY_RUN: bail out after env-driven init
    dry_flag = os.getenv("DRY_RUN")
    if dry_flag is not None and dry_flag.strip().lower() in ("1", "true", "yes", "on"):
        try:
            print("DRY_RUN active: exiting before simulation")
            print(f" testing_mode={getattr(p, 'TESTING_MODE', None)}")
            print(f" NUM_NODES={getattr(p, 'NUM_NODES', 'n/a')}, MINERS_PORTION={getattr(p, 'MINERS_PORTION', 'n/a')}")
            print(f" simTime={getattr(p, 'simTime', 'n/a')}, Binterval={getattr(p, 'Binterval', 'n/a')}")
            print(f" hasSmartContracts={getattr(p, 'hasSmartContracts', 'n/a')}, hasPermissions={getattr(p, 'hasPermissions', 'n/a')}")
        except Exception as e:
            print(f"DRY_RUN summary error: {e}")
        return
    print("START SIMULATION >> Improved Smart Contract & Permissioned Blockchain")
    
    # Initialize permissions and smart contracts
    if hasattr(p, 'hasPermissions') and p.hasPermissions:
        # Assign roles to nodes
        for node in p.NODES:
            if hasattr(p, 'NODE_ROLES') and node.id in p.NODE_ROLES:
                node.update_role(p.NODE_ROLES[node.id])
                print(f"Node {node.id} assigned role: {node.role}")
    
    # Deploy initial smart contracts
    if hasattr(p, 'hasSmartContracts') and p.hasSmartContracts:
        # Deploy audit and privacy contracts
        admin_nodes = [node for node in p.NODES if hasattr(node, 'role') and node.role == "ADMIN"]
        if admin_nodes:
            admin = admin_nodes[0]
            
            # Deploy redaction audit contract
            audit_contract_code = """
            contract RedactionAudit {
                struct RedactionRecord {
                    address requester;
                    uint256 timestamp;
                    string reason;
                    bytes32 originalHash;
                    bytes32 newHash;
                    bool approved;
                }
                mapping(bytes32 => RedactionRecord) public redactions;
                function requestRedaction(bytes32 _id, string _reason) public;
                function approveRedaction(bytes32 _id) public;
            }
            """
            audit_address = admin.deploy_contract(audit_contract_code, "AUDIT")
            if audit_address:
                p.DEPLOYED_CONTRACTS.append(audit_address)
                print(f"Deployed audit contract at: {audit_address}")
            
            # Deploy privacy compliance contract
            privacy_contract_code = """
            contract DataPrivacy {
                struct PrivacyPolicy {
                    uint256 retentionPeriod;
                    bool allowRedaction;
                    address[] authorizedRedactors;
                }
                mapping(address => PrivacyPolicy) public policies;
                function setPrivacyPolicy(uint256 _retention, bool _allowRedaction) public;
                function checkRedactionPermission(address _requester) public view returns (bool);
            }
            """
            privacy_address = admin.deploy_contract(privacy_contract_code, "PRIVACY")
            if privacy_address:
                p.DEPLOYED_CONTRACTS.append(privacy_address)
                print(f"Deployed privacy contract at: {privacy_address}")
    
    for i in range(p.Runs):
        t1 = time.time()
        clock = 0  # set clock to 0 at the start of the simulation
        
        if p.hasTrans:
            if p.Ttechnique == "Light":
                LT.create_transactions()  # generate pending transactions
            elif p.Ttechnique == "Full":
                FT.create_transactions()  # generate pending transactions

        # if has multiplayer in the secret sharing
        # if p.hasMulti:
        #     BlockCommit.setupSecretSharing()
        #     for i in p.NODES:
        #         print(f'NODE {i.id}: Public Key: {i.PK}, Secret Key: {i.SK}')

        Node.generate_genesis_block()  # generate the genesis block for all miners
        # initiate initial events >= 1 to start with
        BlockCommit.generate_initial_events()

        while not Queue.isEmpty() and clock <= p.simTime:
            next_event = Queue.get_next_event()
            clock = next_event.time  # move clock to the time of the event
            BlockCommit.handle_event(next_event)
            Queue.remove_event(next_event)

        # test for chameleon hash forging
        if p.hasRedact:
            print("\n" + "="*60)
            print("  REDACTION OPERATIONS - BEFORE/AFTER ANALYSIS")
            print("="*60)
            
            Consensus.fork_resolution()
            
            # Capture blockchain state BEFORE redaction
            print("\n--- BLOCKCHAIN STATE BEFORE REDACTION ---")
            Statistics.original_global_chain()
            
            # Print pre-redaction statistics
            total_blocks_before = len([node.blockchain for node in p.NODES if node.hashPower > 0][0])
            total_txs_before = sum(len(block.transactions) for block in Statistics.chain if hasattr(block, 'transactions'))
            print(f"Total Blocks Before Redaction: {total_blocks_before}")
            print(f"Total Transactions Before Redaction: {total_txs_before}")
            
            # Show sample blocks before redaction
            sample_node = [node for node in p.NODES if node.hashPower > 0][0]
            if len(sample_node.blockchain) > 3:
                print(f"\nSample Block Before Redaction (Block {len(sample_node.blockchain)//2}):")
                sample_block = sample_node.blockchain[len(sample_node.blockchain)//2]
                print(f"  Block ID: {sample_block.id}")
                print(f"  Transactions: {len(sample_block.transactions)}")
                if hasattr(sample_block, 'r'):
                    print(f"  Randomness (r): {sample_block.r}")
                if sample_block.transactions:
                    print(f"  Sample Transaction IDs: {[tx.id for tx in sample_block.transactions[:3]]}")
            
            # Perform redaction operations
            print(f"\n--- PERFORMING {p.redactRuns} REDACTION OPERATIONS ---")
            BlockCommit.generate_redaction_event(p.redactRuns)
            
            # Capture blockchain state AFTER redaction
            print("\n--- BLOCKCHAIN STATE AFTER REDACTION ---")
            total_blocks_after = len(sample_node.blockchain)
            total_txs_after = sum(len(block.transactions) for block in sample_node.blockchain)
            print(f"Total Blocks After Redaction: {total_blocks_after}")
            print(f"Total Transactions After Redaction: {total_txs_after}")
            
            # Show the same sample block after redaction
            if len(sample_node.blockchain) > 3:
                print(f"\nSample Block After Redaction (Block {len(sample_node.blockchain)//2}):")
                sample_block_after = sample_node.blockchain[len(sample_node.blockchain)//2]
                print(f"  Block ID: {sample_block_after.id}")
                print(f"  Transactions: {len(sample_block_after.transactions)}")
                if hasattr(sample_block_after, 'r'):
                    print(f"  Randomness (r): {sample_block_after.r}")
                if sample_block_after.transactions:
                    print(f"  Sample Transaction IDs: {[tx.id for tx in sample_block_after.transactions[:3]]}")
            
            # Show redaction summary
            print(f"\n--- REDACTION SUMMARY ---")
            redacted_count = sum(len(node.redacted_tx) for node in p.NODES)
            print(f"Total Redacted Transactions: {redacted_count}")
            print(f"Transaction Count Change: {total_txs_before} -> {total_txs_after} (Delta: {total_txs_after - total_txs_before})")
            
            # Show specific redacted transactions
            if redacted_count > 0:
                print(f"\nRedacted Transaction Details:")
                for node in p.NODES:
                    if len(node.redacted_tx) > 0:
                        for redaction in node.redacted_tx[-min(3, len(node.redacted_tx)):]:  # Show last 3 redactions
                            block_depth, tx, reward, time_ms, chain_length, tx_count = redaction
                            print(f"  Node {node.id}: Block {block_depth}, TX ID {tx.id}, Time: {time_ms:.2f}ms")
            
            print("="*60)
        
        Consensus.fork_resolution()  # apply the longest chain to resolve the forks
        Incentives.distribute_rewards()  # distribute the rewards between the participating nodes
        t2 = time.time()
        t = (t2 -t1)* 1000
        print(f"Total time = {t}")

        # calculate the simulation results (e.g., block statistics and miners' rewards)
        Statistics.calculate(t)
        
        # Print smart contract statistics
        if hasattr(p, 'hasSmartContracts') and p.hasSmartContracts:
            print(f"Deployed contracts: {len(p.DEPLOYED_CONTRACTS)}")
            
        # Print redaction statistics
        if hasattr(p, 'hasPermissions') and p.hasPermissions:
            total_redaction_requests = sum(len(node.redaction_requests) for node in p.NODES)
            print(f"Total redaction requests: {total_redaction_requests}")

        ########## reset all global variable before the next run #############
        Statistics.reset()  # reset all variables used to calculate the results
        Node.resetState()  # reset all the states (blockchains) for all nodes in the network
        fname = "{0}M_{1}_{2}K.xlsx".format(
            p.Bsize/1000000, p.Tn/1000, p.Tsize)
        # print all the simulation results in an excel file
        Statistics.print_to_excel(fname)
        Statistics.reset2()  # reset profit results


######################################################## Run Main method #####################################################################
if __name__ == '__main__':
    main()
