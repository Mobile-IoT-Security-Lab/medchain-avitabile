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
            Consensus.fork_resolution()
            Statistics.original_global_chain()
            BlockCommit.generate_redaction_event(p.redactRuns)
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
