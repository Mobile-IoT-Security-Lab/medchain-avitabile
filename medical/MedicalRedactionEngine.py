"""
Enhanced Smart Contract Integration for Data Redaction
====================================================

This module enhances the smart contract system with SNARK proofs and consistency verification
for the "Data Redaction in Smart-Contract-Enabled Permissioned Blockchains" implementation.
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import copy

from ZK.SNARKs import RedactionSNARKManager, ZKProof
from ZK.ProofOfConsistency import ConsistencyProofGenerator, ConsistencyCheckType, ConsistencyProof
from Models.SmartContract import SmartContract, RedactionPolicy
from adapters.config import env_bool

try:
    # Optional adapters; only used if env flags are set
    from adapters.snark import SnarkClient  # type: ignore
except Exception:  # pragma: no cover - optional import
    SnarkClient = None  # type: ignore

try:
    from adapters.evm import EVMClient  # type: ignore
except Exception:  # pragma: no cover - optional import
    EVMClient = None  # type: ignore


@dataclass
class RedactionRequest:
    """Enhanced redaction request with SNARK and consistency proofs."""
    request_id: str
    target_contract: str
    target_function: str
    target_data_field: str
    redaction_type: str  # DELETE, MODIFY, ANONYMIZE
    requester: str
    reason: str
    timestamp: int
    approval_threshold: int
    approvals: List[str]
    zk_proof: Optional[ZKProof] = None
    consistency_proof: Optional[ConsistencyProof] = None
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED, EXECUTED


@dataclass
class MedicalDataRecord:
    """Medical data record structure for the healthcare use case."""
    patient_id: str
    patient_name: str
    medical_record_number: str
    diagnosis: str
    treatment: str
    physician: str
    timestamp: int
    privacy_level: str  # PUBLIC, PRIVATE, CONFIDENTIAL, RESTRICTED
    consent_status: bool
    ipfs_hash: Optional[str] = None
    

class MedicalDataContract(SmartContract):
    """Smart contract for managing medical data with redaction capabilities."""
    
    def __init__(self):
        super().__init__(
            code=self._get_medical_contract_code(),
            is_redactable=True,
            redaction_policies=[
                RedactionPolicy(
                    policy_id="GDPR_RIGHT_TO_ERASURE",
                    policy_type="DELETE",
                    conditions={"patient_consent_withdrawn": True},
                    authorized_roles=["ADMIN", "REGULATOR", "PHYSICIAN"],
                    min_approvals=2,
                    time_lock=86400  # 24 hours
                ),
                RedactionPolicy(
                    policy_id="HIPAA_ANONYMIZATION",
                    policy_type="ANONYMIZE",
                    conditions={"research_purpose": True, "anonymization_required": True},
                    authorized_roles=["ADMIN", "RESEARCHER"],
                    min_approvals=3,
                    time_lock=86400 * 7  # 7 days
                ),
                RedactionPolicy(
                    policy_id="SECURITY_BREACH_REDACTION",
                    policy_type="MODIFY",
                    conditions={"security_breach": True, "data_compromised": True},
                    authorized_roles=["ADMIN"],
                    min_approvals=1,
                    time_lock=0  # Immediate
                )
            ]
        )
        self.state = {
            "medical_records": {},  # patient_id -> MedicalDataRecord
            "consent_records": {},  # patient_id -> consent_status
            "access_logs": [],      # Log of all data access
            "redaction_history": [],  # History of redaction operations
            "ipfs_mappings": {},     # patient_id -> IPFS hash
            "record_integrity": {}   # patient_id -> {original_hash, current_hash, versions: []}
        }
    
    def _get_medical_contract_code(self) -> str:
        """Get the Solidity-like code for the medical data contract."""
        return """
        pragma solidity ^0.8.0;

        contract MedicalDataManager {
            struct MedicalRecord {
                string patientId;
                string patientName;
                string medicalRecordNumber;
                string diagnosis;
                string treatment;
                string physician;
                uint256 timestamp;
                string privacyLevel;
                bool consentStatus;
                string ipfsHash;
            }
            
            struct RedactionRecord {
                string requestId;
                string patientId;
                string redactionType;
                string reason;
                address requester;
                uint256 timestamp;
                bool executed;
                bytes32 zkProofHash;
                bytes32 consistencyProofHash;
            }
            
            mapping(string => MedicalRecord) public medicalRecords;
            mapping(string => bool) public consentStatus;
            mapping(string => RedactionRecord[]) public redactionHistory;
            mapping(address => bool) public authorizedUsers;
            
            event DataStored(string patientId, string ipfsHash, uint256 timestamp);
            event DataRedacted(string patientId, string redactionType, address requester);
            event ConsentUpdated(string patientId, bool newStatus);
            event IPFSHashUpdated(string patientId, string oldHash, string newHash);
            
            modifier onlyAuthorized() {
                require(authorizedUsers[msg.sender], "Not authorized");
                _;
            }
            
            modifier withValidConsent(string memory patientId) {
                require(consentStatus[patientId], "Patient consent required");
                _;
            }
            
            function storeMedicalData(
                string memory patientId,
                string memory patientName,
                string memory diagnosis,
                string memory treatment,
                string memory physician,
                string memory ipfsHash
            ) public onlyAuthorized withValidConsent(patientId) {
                // TODO: Implementation for storing medical data
            }
            
            function requestDataRedaction(
                string memory patientId,
                string memory redactionType,
                string memory reason,
                bytes32 zkProofHash,
                bytes32 consistencyProofHash
            ) public onlyAuthorized returns (string memory requestId) {
                // TODO: Implementation for requesting redaction with proofs
            }
            
            function executeRedaction(
                string memory requestId
            ) public onlyAuthorized returns (bool success) {
                // TODO: Implementation for executing approved redaction
            }
            
            function updateIPFSHash(
                string memory patientId,
                string memory newIpfsHash
            ) public onlyAuthorized {
                // TODO: Implementation for updating IPFS hash after redaction
            }
            
            function withdrawConsent(
                string memory patientId
            ) public {
                // TODO: Implementation for patient to withdraw consent
            }
            
            function queryMedicalData(
                string memory patientId
            ) public view withValidConsent(patientId) returns (MedicalRecord memory) {
                // TODO: Implementation for querying medical data
            }
        }
        """


class EnhancedRedactionEngine:
    """Enhanced redaction engine with SNARK proofs and consistency verification."""
    
    def __init__(self):
        # Feature toggles
        self._use_real_snark = env_bool("USE_REAL_SNARK", False)
        self._use_real_evm = env_bool("USE_REAL_EVM", False)

        # SNARK backend: real (if available) or simulated
        if self._use_real_snark and SnarkClient is not None:
            try:
                self.snark_client = SnarkClient()
            except Exception:
                self.snark_client = None
                self._use_real_snark = False
        else:
            self.snark_client = None

        self.snark_manager = RedactionSNARKManager()
        self.consistency_generator = ConsistencyProofGenerator()
        self.medical_contract = MedicalDataContract()
        
        # EVM backend (scaffold): if enabled, prepare client (no-op if not configured)
        if self._use_real_evm and EVMClient is not None:
            try:
                self.evm_client = EVMClient()  # connect later when needed
            except Exception:
                self.evm_client = None
                self._use_real_evm = False
        else:
            self.evm_client = None
        self.redaction_requests = {}  # request_id -> RedactionRequest
        self.executed_redactions = []
        
    def create_medical_data_record(self, patient_data: Dict[str, Any]) -> MedicalDataRecord:
        """Create a new medical data record."""
        return MedicalDataRecord(
            patient_id=patient_data["patient_id"],
            patient_name=patient_data["patient_name"],
            medical_record_number=patient_data.get("medical_record_number", ""),
            diagnosis=patient_data.get("diagnosis", ""),
            treatment=patient_data.get("treatment", ""),
            physician=patient_data.get("physician", ""),
            timestamp=int(time.time()),
            privacy_level=patient_data.get("privacy_level", "PRIVATE"),
            consent_status=patient_data.get("consent_status", True),
            ipfs_hash=patient_data.get("ipfs_hash", None)
        )
    
    def store_medical_data(self, medical_record: MedicalDataRecord) -> bool:
        """Store medical data in the smart contract."""
        try:
            # Store in contract state
            self.medical_contract.state["medical_records"][medical_record.patient_id] = medical_record
            self.medical_contract.state["consent_records"][medical_record.patient_id] = medical_record.consent_status
            
            if medical_record.ipfs_hash:
                self.medical_contract.state["ipfs_mappings"][medical_record.patient_id] = medical_record.ipfs_hash
            
            # Compute and persist integrity hashes
            record_dict = medical_record.__dict__.copy()
            record_hash = hashlib.sha256(json.dumps(record_dict, sort_keys=True).encode()).hexdigest()
            self.medical_contract.state["record_integrity"][medical_record.patient_id] = {
                "original_hash": record_hash,
                "current_hash": record_hash,
                "versions": [record_hash]
            }
            
            # Log access
            self.medical_contract.state["access_logs"].append({
                "action": "STORE",
                "patient_id": medical_record.patient_id,
                "timestamp": medical_record.timestamp,
                "privacy_level": medical_record.privacy_level
            })
            
            print(f" Medical data stored for patient {medical_record.patient_id}")
            return True
            
        except Exception as e:
            print(f" Failed to store medical data: {e}")
            return False
    
    def request_data_redaction(
        self,
        patient_id: str,
        redaction_type: str,
        reason: str,
        requester: str,
        requester_role: str = "USER"
    ) -> Optional[str]:
        """Request redaction of medical data with SNARK proof."""
        
        try:
            # Check if patient exists
            if patient_id not in self.medical_contract.state["medical_records"]:
                print(f" Patient {patient_id} not found")
                return None
            
            # Enforce role authorization based on policy
            policy = self._get_policy_for_type(redaction_type)
            if policy and requester_role not in policy.authorized_roles:
                print(f" Requester role {requester_role} not authorized for {redaction_type}")
                return None
            
            # Generate request ID
            request_id = f"redaction_{patient_id}_{int(time.time())}_{hash(requester) % 10000}"
            
            # Get current medical record
            current_record = self.medical_contract.state["medical_records"][patient_id]
            
            # Prepare redaction request data for SNARK proof
            redaction_request_data = {
                "request_id": request_id,
                "redaction_type": redaction_type,
                "target_block": 0,  # Contract-based, not block-based
                "target_tx": 0,
                "requester": requester,
                "requester_role": requester_role,
                "original_data": json.dumps(current_record.__dict__),
                "redacted_data": self._generate_redacted_data(current_record, redaction_type),
                "merkle_root": "medical_contract_root",
                "policy_hash": self._get_applicable_policy_hash(redaction_type),
                "signature": f"sig_{requester}_{request_id}"
            }
            
            # Generate SNARK proof (real if enabled & available, else simulated)
            zk_proof: Optional[ZKProof]
            if self._use_real_snark and self.snark_client is not None:
                real = self.snark_client.prove_redaction(
                    {k: redaction_request_data[k] for k in [
                        "redaction_type","target_block","target_tx","requester","requester_role",
                        "merkle_root","policy_hash"
                    ]},
                    {k: redaction_request_data[k] for k in [
                        "request_id","original_data","redacted_data"
                    ]}
                )
                # For now, wrap minimal real-proof artifact into simulated ZKProof shell
                if real:
                    zk_proof = self.snark_manager.circuit.generate_proof(
                        {"operation_type": redaction_request_data["redaction_type"],
                         "merkle_root": redaction_request_data.get("merkle_root","")},
                        {"operation_id": redaction_request_data["request_id"],
                         "redactor_key": redaction_request_data["requester"]}
                    )
                else:
                    zk_proof = self.snark_manager.create_redaction_proof(redaction_request_data)
            else:
                zk_proof = self.snark_manager.create_redaction_proof(redaction_request_data)
            
            if not zk_proof:
                print(f" Failed to generate SNARK proof for redaction request")
                return None
            
            # Generate consistency proof
            pre_state = {"contract_states": {self.medical_contract.address: self.medical_contract.state}}
            post_state = self._simulate_redaction_state(current_record, redaction_type)
            operation_details = {
                "type": "REDACT_CONTRACT_DATA",
                "redacted_fields": self._get_redacted_fields(redaction_type),
                "affected_contracts": [self.medical_contract.address],
                "block_range": (0, 1)
            }
            
            consistency_proof = self.consistency_generator.generate_consistency_proof(
                ConsistencyCheckType.SMART_CONTRACT_STATE,
                pre_state,
                post_state,
                operation_details
            )
            
            # Determine approval threshold based on policy
            approval_threshold = self._get_approval_threshold(redaction_type)
            
            # Create redaction request
            redaction_request = RedactionRequest(
                request_id=request_id,
                target_contract=self.medical_contract.address,
                target_function="requestDataRedaction",
                target_data_field=patient_id,
                redaction_type=redaction_type,
                requester=requester,
                reason=reason,
                timestamp=int(time.time()),
                approval_threshold=approval_threshold,
                approvals=[],
                zk_proof=zk_proof,
                consistency_proof=consistency_proof,
                status="PENDING"
            )
            
            # Store request
            self.redaction_requests[request_id] = redaction_request
            
            print(f" Redaction request {request_id} created with SNARK proof {zk_proof.proof_id}")
            return request_id
            
        except Exception as e:
            print(f" Failed to create redaction request: {e}")
            return None
    
    def approve_redaction(self, request_id: str, approver: str, comments: str = "") -> bool:
        """Approve a redaction request."""
        
        if request_id not in self.redaction_requests:
            print(f" Redaction request {request_id} not found")
            return False
        
        request = self.redaction_requests[request_id]
        
        if approver in request.approvals:
            print(f" Approver {approver} has already approved request {request_id}")
            return False
        
        # Add approval
        request.approvals.append(approver)
        
        # Check if threshold is met
        if len(request.approvals) >= request.approval_threshold:
            request.status = "APPROVED"
            print(f" Redaction request {request_id} approved ({len(request.approvals)}/{request.approval_threshold})")
            
            # Auto-execute if approved
            return self.execute_redaction(request_id)
        else:
            print(f" Redaction request {request_id} approval added ({len(request.approvals)}/{request.approval_threshold})")
            return True
    
    def execute_redaction(self, request_id: str) -> bool:
        """Execute an approved redaction request."""
        
        if request_id not in self.redaction_requests:
            print(f" Redaction request {request_id} not found")
            return False
        
        request = self.redaction_requests[request_id]
        
        if request.status != "APPROVED":
            print(f" Redaction request {request_id} not approved")
            return False
        
        try:
            # Verify SNARK proof before execution
            public_inputs = {
                "operation_type": request.redaction_type,
                "target_block": 0,
                "target_tx": 0,
                "merkle_root": "medical_contract_root",
                "policy_hash": self._get_applicable_policy_hash(request.redaction_type)
            }
            
            if not self.snark_manager.verify_redaction_proof(request.zk_proof, public_inputs):
                print(f" SNARK proof verification failed for request {request_id}")
                return False
            
            # Get current record
            patient_id = request.target_data_field
            current_record = self.medical_contract.state["medical_records"][patient_id]
            
            # Integrity: capture pre-hash
            current_dict = current_record.copy() if isinstance(current_record, dict) else current_record.__dict__.copy()
            pre_hash = hashlib.sha256(json.dumps(current_dict, sort_keys=True).encode()).hexdigest()
            
            # Execute redaction
            if request.redaction_type == "DELETE":
                # Remove patient data
                self.medical_contract.state["medical_records"].pop(patient_id, None)
                self.medical_contract.state["consent_records"].pop(patient_id, None)
                self.medical_contract.state["ipfs_mappings"].pop(patient_id, None)
                # Update integrity registry
                integ = self.medical_contract.state["record_integrity"].get(patient_id, {})
                if integ:
                    integ.setdefault("versions", []).append(pre_hash)
                    integ["current_hash"] = None
                    integ["deleted"] = True
                    
            elif request.redaction_type == "ANONYMIZE":
                # Anonymize sensitive fields
                if isinstance(current_record, dict):
                    current_record["patient_name"] = "[REDACTED]"
                    current_record["medical_record_number"] = "[REDACTED]"
                    current_record["physician"] = "[REDACTED]"
                    self.medical_contract.state["medical_records"][patient_id] = current_record
                else:
                    current_record.patient_name = "[REDACTED]"
                    current_record.medical_record_number = "[REDACTED]"
                    current_record.physician = "[REDACTED]"
                # Update integrity registry
                updated = self.medical_contract.state["medical_records"][patient_id]
                updated_dict = updated if isinstance(updated, dict) else updated.__dict__
                post_hash = hashlib.sha256(json.dumps(updated_dict, sort_keys=True).encode()).hexdigest()
                integ = self.medical_contract.state["record_integrity"].get(patient_id, {})
                if integ:
                    integ.setdefault("versions", []).append(post_hash)
                    integ["current_hash"] = post_hash
                
            elif request.redaction_type == "MODIFY":
                # Modify specific fields based on reason
                reason_l = request.reason.lower()
                if isinstance(current_record, dict):
                    if "diagnosis" in reason_l:
                        current_record["diagnosis"] = "[MODIFIED]"
                    if "treatment" in reason_l:
                        current_record["treatment"] = "[MODIFIED]"
                    self.medical_contract.state["medical_records"][patient_id] = current_record
                else:
                    if "diagnosis" in reason_l:
                        current_record.diagnosis = "[MODIFIED]"
                    if "treatment" in reason_l:
                        current_record.treatment = "[MODIFIED]"
                # Update integrity registry
                updated = self.medical_contract.state["medical_records"][patient_id]
                updated_dict = updated if isinstance(updated, dict) else updated.__dict__
                post_hash = hashlib.sha256(json.dumps(updated_dict, sort_keys=True).encode()).hexdigest()
                integ = self.medical_contract.state["record_integrity"].get(patient_id, {})
                if integ:
                    integ.setdefault("versions", []).append(post_hash)
                    integ["current_hash"] = post_hash
            
            # Update redaction history
            redaction_record = {
                "request_id": request_id,
                "patient_id": patient_id,
                "redaction_type": request.redaction_type,
                "reason": request.reason,
                "requester": request.requester,
                "approvers": request.approvals,
                "timestamp": int(time.time()),
                "zk_proof_id": request.zk_proof.proof_id,
                "consistency_proof_id": request.consistency_proof.proof_id,
                "pre_hash": pre_hash,
                "post_hash": self.medical_contract.state["record_integrity"].get(patient_id, {}).get("current_hash")
            }
            
            self.medical_contract.state["redaction_history"].append(redaction_record)
            self.executed_redactions.append(redaction_record)
            
            # Update request status
            request.status = "EXECUTED"
            
            print(f" Redaction request {request_id} executed successfully")
            print(f"   Type: {request.redaction_type}")
            print(f"   Patient: {patient_id}")
            print(f"   SNARK Proof: {request.zk_proof.proof_id}")
            print(f"   Consistency Proof: {request.consistency_proof.proof_id}")
            
            return True
            
        except Exception as e:
            print(f" Failed to execute redaction request {request_id}: {e}")
            return False
    
    def query_medical_data(self, patient_id: str, requester: str) -> Optional[MedicalDataRecord]:
        """Query medical data with access control."""
        
        # Check consent
        if patient_id not in self.medical_contract.state["consent_records"]:
            print(f" Patient {patient_id} not found")
            return None
        
        if not self.medical_contract.state["consent_records"][patient_id]:
            print(f" Patient {patient_id} has withdrawn consent")
            return None
        
        # Get record
        if patient_id in self.medical_contract.state["medical_records"]:
            record = self.medical_contract.state["medical_records"][patient_id]
            if isinstance(record, dict):
                record = MedicalDataRecord(**record)
            
            # Log access
            self.medical_contract.state["access_logs"].append({
                "action": "QUERY",
                "patient_id": patient_id,
                "requester": requester,
                "timestamp": int(time.time())
            })
            
            return record
        
        return None
    
    def get_redaction_history(self, patient_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get redaction history for a patient or all patients."""
        
        history = self.medical_contract.state["redaction_history"]
        
        if patient_id:
            return [r for r in history if r["patient_id"] == patient_id]
        
        return history
    
    def _generate_redacted_data(self, record: MedicalDataRecord, redaction_type: str) -> str:
        """Generate redacted version of medical data."""
        
        redacted_record = record.__dict__.copy()
        
        if redaction_type == "DELETE":
            return json.dumps({})
        elif redaction_type == "ANONYMIZE":
            redacted_record["patient_name"] = "[REDACTED]"
            redacted_record["medical_record_number"] = "[REDACTED]"
            redacted_record["physician"] = "[REDACTED]"
        elif redaction_type == "MODIFY":
            redacted_record["diagnosis"] = "[MODIFIED]"
            redacted_record["treatment"] = "[MODIFIED]"
        
        return json.dumps(redacted_record)
    
    def _simulate_redaction_state(self, record: MedicalDataRecord, redaction_type: str) -> Dict[str, Any]:
        """Simulate the contract state after redaction."""
        
        simulated_state = copy.deepcopy(self.medical_contract.state)
        
        if redaction_type == "DELETE":
            if record.patient_id in simulated_state["medical_records"]:
                del simulated_state["medical_records"][record.patient_id]
        else:
            # Modify the record
            modified_record = record.__dict__.copy()
            if redaction_type == "ANONYMIZE":
                modified_record["patient_name"] = "[REDACTED]"
                modified_record["medical_record_number"] = "[REDACTED]"
                modified_record["physician"] = "[REDACTED]"
            
            simulated_state["medical_records"][record.patient_id] = modified_record
        
        return {"contract_states": {self.medical_contract.address: simulated_state}}
    
    def _get_redacted_fields(self, redaction_type: str) -> List[str]:
        """Get list of fields that will be redacted."""
        
        if redaction_type == "DELETE":
            return ["patient_name", "medical_record_number", "diagnosis", "treatment", "physician"]
        elif redaction_type == "ANONYMIZE":
            return ["patient_name", "medical_record_number", "physician"]
        elif redaction_type == "MODIFY":
            return ["diagnosis", "treatment"]
        
        return []
    
    def _get_applicable_policy_hash(self, redaction_type: str) -> str:
        """Get hash of applicable redaction policy."""
        
        policy_mapping = {
            "DELETE": "GDPR_RIGHT_TO_ERASURE",
            "ANONYMIZE": "HIPAA_ANONYMIZATION", 
            "MODIFY": "SECURITY_BREACH_REDACTION"
        }
        
        policy_id = policy_mapping.get(redaction_type, "DEFAULT")
        return hashlib.sha256(policy_id.encode()).hexdigest()
    
    def _get_approval_threshold(self, redaction_type: str) -> int:
        """Get approval threshold for redaction type."""
        policy = self._get_policy_for_type(redaction_type)
        if policy:
            return policy.min_approvals
        return 2

    def _get_policy_for_type(self, redaction_type: str) -> Optional[RedactionPolicy]:
        for pol in getattr(self.medical_contract, "redaction_policies", []):
            if getattr(pol, "policy_type", "") == redaction_type:
                return pol
        return None


# Testing and demonstration
def test_enhanced_medical_redaction():
    """Test the enhanced medical data redaction system."""
    
    print("\n Testing Enhanced Medical Data Redaction System")
    print("=" * 60)
    
    # Initialize redaction engine
    engine = EnhancedRedactionEngine()
    
    # Create sample medical records
    sample_patients = [
        {
            "patient_id": "PAT_001",
            "patient_name": "John Doe",
            "medical_record_number": "MRN_12345",
            "diagnosis": "Type 2 Diabetes",
            "treatment": "Metformin 500mg twice daily",
            "physician": "Dr. Sarah Johnson",
            "privacy_level": "PRIVATE",
            "consent_status": True,
            "ipfs_hash": "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG"
        },
        {
            "patient_id": "PAT_002", 
            "patient_name": "Jane Smith",
            "medical_record_number": "MRN_67890",
            "diagnosis": "Hypertension",
            "treatment": "Lisinopril 10mg daily",
            "physician": "Dr. Michael Chen",
            "privacy_level": "CONFIDENTIAL",
            "consent_status": True,
            "ipfs_hash": "QmPZ9gcCEpqKTo6aq61g4nD2v7AiHNleLGUh4EF5yNRJv5"
        }
    ]
    
    # Store medical data
    print("\n Storing medical data...")
    for patient_data in sample_patients:
        record = engine.create_medical_data_record(patient_data)
        engine.store_medical_data(record)
    
    # Test querying data
    print("\n Querying medical data...")
    record = engine.query_medical_data("PAT_001", "researcher_001")
    if record:
        print(f"  Patient: {record.patient_name}")
        print(f"  Diagnosis: {record.diagnosis}")
        print(f"  IPFS Hash: {record.ipfs_hash}")
    
    # Test redaction request with SNARK proof
    print("\n Testing GDPR data deletion request...")
    request_id = engine.request_data_redaction(
        patient_id="PAT_001",
        redaction_type="DELETE",
        reason="Patient requested data deletion under GDPR Article 17",
        requester="regulator_001",
        requester_role="REGULATOR"
    )
    
    if request_id:
        print(f"  Request ID: {request_id}")
        
        # Get request details
        request = engine.redaction_requests[request_id]
        print(f"  SNARK Proof ID: {request.zk_proof.proof_id}")
        print(f"  Consistency Proof ID: {request.consistency_proof.proof_id}")
        print(f"  Approval Threshold: {request.approval_threshold}")
        
        # Approve the request
        print("\n Approving redaction request...")
        engine.approve_redaction(request_id, "admin_001", "GDPR compliance approved")
        engine.approve_redaction(request_id, "regulator_002", "Privacy assessment completed")
        
        # Check if patient data is deleted
        print("\n Verifying data deletion...")
        deleted_record = engine.query_medical_data("PAT_001", "researcher_001")
        if deleted_record is None:
            print("   Patient data successfully deleted")
        else:
            print("   Patient data still exists")
    
    # Test anonymization request
    print("\n Testing HIPAA anonymization request...")
    anon_request_id = engine.request_data_redaction(
        patient_id="PAT_002",
        redaction_type="ANONYMIZE",
        reason="Research data anonymization for clinical study",
        requester="researcher_001",
        requester_role="RESEARCHER"
    )
    
    if anon_request_id:
        # Approve anonymization
        engine.approve_redaction(anon_request_id, "admin_001", "Research approved")
        engine.approve_redaction(anon_request_id, "regulator_001", "Anonymization verified")
        engine.approve_redaction(anon_request_id, "researcher_lead", "Research ethics approved")
        
        # Check anonymized data
        print("\n Verifying data anonymization...")
        anon_record = engine.query_medical_data("PAT_002", "researcher_001")
        if anon_record:
            print(f"  Patient Name: {anon_record.patient_name}")
            print(f"  Medical Record Number: {anon_record.medical_record_number}")
            print(f"  Physician: {anon_record.physician}")
            print(f"  Diagnosis: {anon_record.diagnosis} (preserved for research)")
    
    # Display redaction history
    print("\n Redaction History:")
    history = engine.get_redaction_history()
    for record in history:
        print(f"  Request: {record['request_id']}")
        print(f"    Patient: {record['patient_id']}")
        print(f"    Type: {record['redaction_type']}")
        print(f"    Reason: {record['reason']}")
        print(f"    SNARK Proof: {record['zk_proof_id']}")
        print(f"    Approvers: {len(record['approvers'])}")
        print()
    
    print(" Enhanced medical redaction system test completed!")


if __name__ == "__main__":
    test_enhanced_medical_redaction()  # TODO: check if I completely and correctly check and test all this file (MedicalRedactionEngine.py)
    # TODO: Add this test to the tests suite
