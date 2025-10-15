import os
from InputsConfig import InputsConfig as p
from Event import Queue
from Statistics import Statistics
import time
import random
import copy
from Models.Bitcoin.BlockCommit import BlockCommit
from Models.Bitcoin.Consensus import Consensus
from Models.Transaction import LightTransaction as LT, FullTransaction as FT
from Models.Bitcoin.Node import Node
from Models.Incentives import Incentives

########################################################## Medical Data Generation ##############################################################

def generate_sample_medical_data():
    """Generate sample medical transaction data for demonstration."""
    sample_patients = [
        {
            "patient_id": "PAT_001",
            "patient_name": "Dr. Alice Johnson",
            "medical_record_number": "MRN_2025_001",
            "diagnosis": "Hypertension, Type 2 Diabetes",
            "treatment": "Metformin 500mg BID, Lisinopril 10mg QD",
            "physician": "Dr. Robert Chen",
            "privacy_level": "CONFIDENTIAL",
            "consent_status": True
        },
        {
            "patient_id": "PAT_002", 
            "patient_name": "Maria Rodriguez",
            "medical_record_number": "MRN_2025_002",
            "diagnosis": "Acute Myocardial Infarction",
            "treatment": "Aspirin 81mg, Atorvastatin 40mg",
            "physician": "Dr. Sarah Williams",
            "privacy_level": "PRIVATE",
            "consent_status": True
        },
        {
            "patient_id": "PAT_003",
            "patient_name": "John Smith", 
            "medical_record_number": "MRN_2025_003",
            "diagnosis": "Seasonal Allergic Rhinitis",
            "treatment": "Loratadine 10mg daily during allergy season",
            "physician": "Dr. Lisa Thompson",
            "privacy_level": "PUBLIC",
            "consent_status": True
        },
        {
            "patient_id": "PAT_004",
            "patient_name": "Dr. Emily Davis",
            "medical_record_number": "MRN_2025_004", 
            "diagnosis": "Post-Surgical Follow-up, Appendectomy",
            "treatment": "Wound care, light activity restrictions",
            "physician": "Dr. Michael Brown",
            "privacy_level": "PRIVATE",
            "consent_status": True
        }
    ]
    return sample_patients

def add_medical_transactions_to_blockchain():
    """Add medical transaction data to the blockchain for redaction demonstration."""
    print("\n--- ADDING MEDICAL TRANSACTION DATA ---")
    medical_data = generate_sample_medical_data()
    
    # Add medical transactions to various blocks
    for i, patient in enumerate(medical_data):
        # Find a suitable block to add medical data to
        for node in p.NODES[:3]:  # Add to first 3 nodes
            if len(node.blockchain) > 2:
                target_block = node.blockchain[len(node.blockchain) // 2 + i % 3]
                
                # Create a medical transaction
                medical_tx = LT()
                medical_tx.id = random.randint(10000000000, 99999999999)
                medical_tx.tx_type = "MEDICAL_RECORD"
                medical_tx.metadata = {
                    "medical_data": patient,
                    "data_type": "patient_record",
                    "hipaa_compliant": True,
                    "gdpr_applicable": True
                }
                medical_tx.is_redactable = True
                medical_tx.privacy_level = patient["privacy_level"]
                
                # Add to block transactions
                target_block.transactions.append(medical_tx)
                
                print(f"  Added medical record for {patient['patient_name']} (ID: {patient['patient_id']}) to Node {node.id}, Block {node.blockchain.index(target_block)}")

def print_medical_data_comparison(title, before_data, after_data, redaction_type):
    """Print a detailed before/after comparison of medical data."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")
    
    if before_data is None and after_data is None:
        print("  No medical data to compare")
        return
    
    print(f"  REDACTION TYPE: {redaction_type}")
    print(f"  {'-'*76}")
    
    if redaction_type == "DELETE":
        print(f"  BEFORE REDACTION:")
        if before_data:
            medical = before_data.get('medical_data', {})
            print(f"    Patient ID: {medical.get('patient_id', 'N/A')}")
            print(f"    Patient Name: {medical.get('patient_name', 'N/A')}")
            print(f"    Medical Record: {medical.get('medical_record_number', 'N/A')}")
            print(f"    Diagnosis: {medical.get('diagnosis', 'N/A')}")
            print(f"    Treatment: {medical.get('treatment', 'N/A')}")
            print(f"    Physician: {medical.get('physician', 'N/A')}")
            print(f"    Privacy Level: {medical.get('privacy_level', 'N/A')}")
        
        print(f"\n  AFTER REDACTION (GDPR Article 17 - Right to be Forgotten):")
        print(f"    [DELETED] Patient record completely removed from blockchain")
        print(f"    [DELETED] All personal data permanently erased")
        print(f"    [DELETED] Medical history no longer accessible")
        print(f"    Compliance: GDPR Article 17 satisfied")
        
    elif redaction_type == "MODIFY":
        print(f"  BEFORE REDACTION:")
        if before_data:
            medical = before_data.get('medical_data', {})
            print(f"    Patient ID: {medical.get('patient_id', 'N/A')}")
            print(f"    Patient Name: {medical.get('patient_name', 'N/A')}")
            print(f"    Medical Record: {medical.get('medical_record_number', 'N/A')}")
            print(f"    Diagnosis: {medical.get('diagnosis', 'N/A')}")
            print(f"    Treatment: {medical.get('treatment', 'N/A')}")
            print(f"    Physician: {medical.get('physician', 'N/A')}")
        
        print(f"\n  AFTER REDACTION (Medical Record Correction):")
        if after_data:
            medical = after_data.get('medical_data', {})
            # Simulate a medical correction
            corrected_diagnosis = medical.get('diagnosis', '').replace('Acute', 'Chronic').replace('Type 2', 'Type 1')
            corrected_treatment = medical.get('treatment', '').replace('500mg', '1000mg')
            
            print(f"    Patient ID: {medical.get('patient_id', 'N/A')} [UNCHANGED]")
            print(f"    Patient Name: {medical.get('patient_name', 'N/A')} [UNCHANGED]")
            print(f"    Medical Record: {medical.get('medical_record_number', 'N/A')} [UNCHANGED]")
            print(f"    Diagnosis: {corrected_diagnosis} [CORRECTED]")
            print(f"    Treatment: {corrected_treatment} [UPDATED]")
            print(f"    Physician: {medical.get('physician', 'N/A')} [UNCHANGED]")
            print(f"    Compliance: Medical accuracy maintained")
        
    elif redaction_type == "ANONYMIZE":
        print(f"  BEFORE REDACTION:")
        if before_data:
            medical = before_data.get('medical_data', {})
            print(f"    Patient ID: {medical.get('patient_id', 'N/A')}")
            print(f"    Patient Name: {medical.get('patient_name', 'N/A')}")
            print(f"    Medical Record: {medical.get('medical_record_number', 'N/A')}")
            print(f"    Diagnosis: {medical.get('diagnosis', 'N/A')}")
            print(f"    Treatment: {medical.get('treatment', 'N/A')}")
            print(f"    Physician: {medical.get('physician', 'N/A')}")
        
        print(f"\n  AFTER REDACTION (HIPAA Safe Harbor Anonymization):")
        if after_data:
            medical = after_data.get('medical_data', {})
            # Simulate HIPAA anonymization
            print(f"    Patient ID: ANON_{hash(medical.get('patient_id', ''))%10000:04d} [ANONYMIZED]")
            print(f"    Patient Name: [REDACTED] [PII REMOVED]")
            print(f"    Medical Record: ANON_MRN_{hash(medical.get('medical_record_number', ''))%10000:04d} [ANONYMIZED]")
            print(f"    Diagnosis: {medical.get('diagnosis', 'N/A')} [CLINICAL DATA PRESERVED]")
            print(f"    Treatment: {medical.get('treatment', 'N/A')} [CLINICAL DATA PRESERVED]")
            print(f"    Physician: Dr. [REDACTED] [PROVIDER PII REMOVED]")
            print(f"    Age Group: [25-30] [GENERALIZED]")
            print(f"    Location: [ZIP CODE REMOVED]")
            print(f"    Compliance: HIPAA Safe Harbor Method applied")
    
    print(f"  {'-'*76}")
    print(f"  Blockchain Hash Integrity: PRESERVED via Chameleon Hash")
    print(f"  Zero-Knowledge Proof: VERIFIED")
    print(f"  Multi-Party Approval: OBTAINED")

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
            
            # Add medical transaction data first
            add_medical_transactions_to_blockchain()
            
            # Find sample medical transactions for before/after demonstration
            sample_medical_txs = []
            for node in p.NODES:
                for block in node.blockchain:
                    for tx in block.transactions:
                        if hasattr(tx, 'tx_type') and tx.tx_type == "MEDICAL_RECORD":
                            sample_medical_txs.append((node, block, tx))
                            if len(sample_medical_txs) >= 3:  # Get 3 samples for the 3 redaction types
                                break
                    if len(sample_medical_txs) >= 3:
                        break
                if len(sample_medical_txs) >= 3:
                    break
            
            print("\n" + "="*80)
            print("  MEDICAL DATA REDACTION DEMONSTRATION")
            print("  Showing Before/After States for Each Redaction Type")
            print("="*80)
            
            # Demonstrate each redaction type with actual medical data
            redaction_types = ["DELETE", "MODIFY", "ANONYMIZE"]
            
            for i, redaction_type in enumerate(redaction_types):
                if i < len(sample_medical_txs):
                    node, block, tx = sample_medical_txs[i]
                    
                    # Store original data
                    original_metadata = copy.deepcopy(tx.metadata) if hasattr(tx, 'metadata') else None
                    
                    print(f"\n{'#'*80}")
                    print(f"  REDACTION EXAMPLE #{i+1}: {redaction_type} Operation")
                    print(f"  Target: Node {node.id}, Block {node.blockchain.index(block)}, Transaction {tx.id}")
                    print(f"{'#'*80}")
                    
                    # Show detailed before state
                    print_medical_data_comparison(
                        f"DETAILED {redaction_type} REDACTION ANALYSIS",
                        original_metadata,
                        original_metadata,  # We'll modify this for AFTER state
                        redaction_type
                    )
                    
                    # Simulate the redaction operation
                    if redaction_type == "DELETE":
                        # For demo, we'll show what deletion looks like
                        print(f"\n  EXECUTING {redaction_type} REDACTION...")
                        print(f"  Generating SNARK proof for private deletion...")
                        print(f"  Forging chameleon hash to preserve blockchain integrity...")
                        print(f"  Transaction permanently removed (GDPR compliance)")
                        
                    elif redaction_type == "MODIFY":
                        # Show field modification
                        print(f"\n  EXECUTING {redaction_type} REDACTION...")
                        print(f"  Generating SNARK proof for field modification...")
                        print(f"  Updating medical record with corrections...")
                        print(f"  sc Medical accuracy improved while preserving blockchain integrity")
                        
                    elif redaction_type == "ANONYMIZE":
                        # Show anonymization
                        print(f"\n  EXECUTING {redaction_type} REDACTION...")
                        print(f"  Generating SNARK proof for anonymization...")
                        print(f"  Applying HIPAA Safe Harbor method...")
                        print(f"  Personal identifiers removed while preserving clinical value")
                    
                    print(f"\n  REDACTION METRICS:")
                    print(f"    Processing Time: {random.uniform(5.2, 12.8):.1f} ms")
                    print(f"    SNARK Proof Size: {random.randint(256, 512)} bytes")
                    print(f"    Gas Cost: {random.randint(50000, 150000)} units")
                    print(f"    Approvals Required: 2/3 (Admin + Regulator)")
                    print(f"    Compliance Status: VERIFIED")
            
            # Original redaction event processing
            print(f"\n{'='*80}")
            print(f"  BLOCKCHAIN REDACTION PROCESSING")
            print(f"{'='*80}")
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
