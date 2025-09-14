"""
IPFS Integration for Medical Data Management
==========================================

This module provides IPFS (InterPlanetary File System) integration for storing and managing
medical datasets in the redactable blockchain system. It supports the "right to be forgotten"
by enabling redaction of both blockchain records and IPFS data.
"""

import json
import hashlib
import time
import random
import os
import base64
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from adapters.config import env_str

try:  # optional dependency present in requirements
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
except Exception:  # pragma: no cover
    AESGCM = None  # type: ignore


@dataclass
class IPFSRecord:
    """IPFS record structure for medical data."""
    ipfs_hash: str
    patient_id: str
    data_type: str  # "medical_record", "lab_result", "imaging", etc.
    content_hash: str  # Hash of the actual content
    timestamp: int
    privacy_level: str
    encryption_key: Optional[str] = None
    access_control: Optional[Dict[str, Any]] = None
    

@dataclass
class MedicalDataset:
    """Medical dataset structure."""
    dataset_id: str
    name: str
    description: str
    patient_records: List[Dict[str, Any]]
    creation_timestamp: int
    last_updated: int
    version: str
    ipfs_hash: Optional[str] = None
    redaction_log: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.redaction_log is None:
            self.redaction_log = []


class FakeIPFSClient:
    """
    Simulated IPFS client for testing and demonstration.
    In production, this would interface with a real IPFS node.
    """
    
    def __init__(self, storage_dir: str = "/tmp/fake_ipfs"):
        self.storage_dir = storage_dir
        self.content_store = {}  # hash -> content
        self.pin_set = set()  # pinned hashes
        
        # Create storage directory
        os.makedirs(storage_dir, exist_ok=True)
        
    def add(self, content: str, pin: bool = True) -> str:
        """Add content to IPFS and return hash."""
        # Generate fake IPFS hash (Qm... format)
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        ipfs_hash = f"Qm{content_hash[:44]}"
        
        # Store content
        self.content_store[ipfs_hash] = content
        
        # Write to file for persistence
        file_path = os.path.join(self.storage_dir, ipfs_hash)
        with open(file_path, 'w') as f:
            f.write(content)
        
        if pin:
            self.pin_set.add(ipfs_hash)
            
        print(f" Added to IPFS: {ipfs_hash}")
        return ipfs_hash
    
    def get(self, ipfs_hash: str) -> Optional[str]:
        """Get content from IPFS by hash."""
        if ipfs_hash in self.content_store:
            return self.content_store[ipfs_hash]
        
        # Try to read from file
        file_path = os.path.join(self.storage_dir, ipfs_hash)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                self.content_store[ipfs_hash] = content
                return content
        
        return None
    
    def pin(self, ipfs_hash: str) -> bool:
        """Pin content to prevent garbage collection."""
        if ipfs_hash in self.content_store:
            self.pin_set.add(ipfs_hash)
            return True
        return False
    
    def unpin(self, ipfs_hash: str) -> bool:
        """Unpin content (allow garbage collection)."""
        if ipfs_hash in self.pin_set:
            self.pin_set.remove(ipfs_hash)
            return True
        return False
    
    def rm(self, ipfs_hash: str) -> bool:
        """Remove content from IPFS (simulated deletion)."""
        # In real IPFS, content is immutable. This simulates redaction.
        if ipfs_hash in self.content_store:
            del self.content_store[ipfs_hash]
            
        # Remove file
        file_path = os.path.join(self.storage_dir, ipfs_hash)
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # Unpin if pinned
        self.unpin(ipfs_hash)
        
        print(f"️  Removed from IPFS: {ipfs_hash}")
        return True
    
    def ls(self) -> List[str]:
        """List all stored hashes."""
        return list(self.content_store.keys())
    
    def stat(self, ipfs_hash: str) -> Optional[Dict[str, Any]]:
        """Get statistics about stored content."""
        if ipfs_hash in self.content_store:
            content = self.content_store[ipfs_hash]
            return {
                "hash": ipfs_hash,
                "size": len(content.encode()),
                "pinned": ipfs_hash in self.pin_set,
                "type": "file"
            }
        return None

    def gateway_url(self, ipfs_hash: str) -> str:
        """Return a pseudo-gateway URL for demo purposes."""
        # Use a recognizable scheme; in real mode, adapters.ipfs.RealIPFSClient supplies real gateway URLs
        return f"ipfs://{ipfs_hash}"


class MedicalDatasetGenerator:
    """Generates fake medical datasets for testing."""
    
    def __init__(self):
        self.patient_names = [
            "Alice Johnson", "Bob Smith", "Carol Williams", "David Brown", "Emma Davis",
            "Frank Miller", "Grace Wilson", "Henry Moore", "Isabel Taylor", "Jack Anderson",
            "Kate Thomas", "Liam Jackson", "Maya White", "Noah Harris", "Olivia Martin",
            "Paul Thompson", "Quinn Garcia", "Ruby Martinez", "Sam Robinson", "Tina Clark"
        ]
        
        self.diagnoses = [
            "Type 2 Diabetes", "Hypertension", "Asthma", "Coronary Artery Disease",
            "COPD", "Depression", "Anxiety Disorder", "Osteoarthritis", "Migraine",
            "Hypothyroidism", "Gastroesophageal Reflux", "Chronic Kidney Disease",
            "Atrial Fibrillation", "Osteoporosis", "Allergic Rhinitis"
        ]
        
        self.treatments = [
            "Metformin 500mg BID", "Lisinopril 10mg daily", "Albuterol inhaler PRN",
            "Atorvastatin 20mg daily", "Sertraline 50mg daily", "Ibuprofen 400mg TID",
            "Omeprazole 20mg daily", "Levothyroxine 75mcg daily", "Aspirin 81mg daily",
            "Amlodipine 5mg daily", "Prednisone 10mg daily", "Warfarin as directed"
        ]
        
        self.physicians = [
            "Dr. Sarah Johnson", "Dr. Michael Chen", "Dr. Emily Rodriguez", "Dr. James Wilson",
            "Dr. Lisa Thompson", "Dr. Robert Garcia", "Dr. Jennifer Martinez", "Dr. David Lee",
            "Dr. Maria Gonzalez", "Dr. Thomas Anderson", "Dr. Amanda Clark", "Dr. Kevin Brown"
        ]
    
    def generate_patient_record(self, patient_id: str) -> Dict[str, Any]:
        """Generate a fake patient medical record."""
        return {
            "patient_id": patient_id,
            "patient_name": random.choice(self.patient_names),
            "medical_record_number": f"MRN_{random.randint(10000, 99999)}",
            "date_of_birth": f"{random.randint(1940, 2005)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "gender": random.choice(["Male", "Female", "Other"]),
            "diagnosis": random.choice(self.diagnoses),
            "treatment": random.choice(self.treatments),
            "physician": random.choice(self.physicians),
            "admission_date": f"{random.randint(2020, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "discharge_date": f"{random.randint(2020, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "insurance_id": f"INS_{random.randint(100000, 999999)}",
            "emergency_contact": f"Contact_{random.randint(1000, 9999)}",
            "allergies": random.choice(["None", "Penicillin", "Shellfish", "Peanuts", "Latex"]),
            "blood_type": random.choice(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]),
            "privacy_level": random.choice(["PRIVATE", "CONFIDENTIAL", "RESTRICTED"]),
            "consent_status": random.choice([True, False]),
            "lab_results": {
                "glucose": random.randint(70, 200),
                "cholesterol": random.randint(150, 300),
                "blood_pressure": f"{random.randint(90, 180)}/{random.randint(60, 120)}"
            }
        }
    
    def generate_dataset(self, num_patients: int = 100, dataset_name: str = "Medical Dataset") -> MedicalDataset:
        """Generate a complete medical dataset."""
        
        patient_records = []
        for i in range(num_patients):
            patient_id = f"PAT_{i+1:04d}"
            record = self.generate_patient_record(patient_id)
            patient_records.append(record)
        
        dataset_id = f"DS_{int(time.time())}_{random.randint(1000, 9999)}"
        
        return MedicalDataset(
            dataset_id=dataset_id,
            name=dataset_name,
            description=f"Generated medical dataset with {num_patients} patient records",
            patient_records=patient_records,
            creation_timestamp=int(time.time()),
            last_updated=int(time.time()),
            version="1.0"
        )


class IPFSMedicalDataManager:
    """Manages medical data storage and redaction in IPFS."""
    
    def __init__(self, ipfs_client: Optional[Any] = None):
        """Manager accepts either the simulated or real IPFS client.

        If no client is provided and USE_REAL_IPFS=1 with a reachable daemon,
        a real client will be used; otherwise the simulated FakeIPFSClient is used.
        """
        if ipfs_client is not None:
            self.ipfs_client = ipfs_client
        else:
            # Best-effort: pick real client if available and enabled by env
            try:
                from adapters.ipfs import get_ipfs_client  # local import to avoid hard dep in tests

                real = get_ipfs_client()
            except Exception:
                real = None

            self.ipfs_client = real or FakeIPFSClient()
        self.dataset_registry = {}  # dataset_id -> dataset_metadata
        self.patient_mappings = {}  # patient_id -> [ipfs_hashes]
        self.redaction_log = []     # Log of all redaction operations
        # Encryption configuration (AES-GCM via IPFS_ENC_KEY base64)
        self._enc_key: Optional[bytes] = self._load_encryption_key()
        self._enc_enabled: bool = self._enc_key is not None and AESGCM is not None
        
    def upload_dataset(self, dataset: MedicalDataset, encrypt: bool = True) -> str:
        """Upload medical dataset to IPFS."""
        
        try:
            # Convert dataset to JSON
            dataset_json = json.dumps(asdict(dataset), indent=2)
            
            # Encrypt if requested and a valid key is configured
            payload: str
            encryption_mode = None
            if encrypt and self._enc_enabled:
                payload = self._encrypt_json(dataset_json)
                encryption_mode = "AES-GCM"
            elif encrypt:
                # Fallback simulated encryption to preserve compatibility when no key provided
                payload = f"ENCRYPTED:{dataset_json}"
                encryption_mode = "SIMULATED"
            else:
                payload = dataset_json
            
            # Upload to IPFS
            ipfs_hash = self.ipfs_client.add(payload, pin=True)
            
            # Update dataset record
            dataset.ipfs_hash = ipfs_hash
            dataset.last_updated = int(time.time())
            
            # Register dataset
            self.dataset_registry[dataset.dataset_id] = {
                "dataset_id": dataset.dataset_id,
                "name": dataset.name,
                "ipfs_hash": ipfs_hash,
                "creation_timestamp": dataset.creation_timestamp,
                "last_updated": dataset.last_updated,
                "version": dataset.version,
                "patient_count": len(dataset.patient_records),
                "encrypted": encrypt,
                "encryption": encryption_mode
            }
            
            # Build patient mappings
            for record in dataset.patient_records:
                patient_id = record["patient_id"]
                if patient_id not in self.patient_mappings:
                    self.patient_mappings[patient_id] = []
                self.patient_mappings[patient_id].append(ipfs_hash)
            
            print(f" Uploaded dataset {dataset.dataset_id} to IPFS: {ipfs_hash}")
            print(f"   Patients: {len(dataset.patient_records)}")
            print(f"   Size: {len(payload)} bytes")
            
            return ipfs_hash
            
        except Exception as e:
            print(f" Failed to upload dataset: {e}")
            return ""
    
    def download_dataset(self, ipfs_hash: str) -> Optional[MedicalDataset]:
        """Download medical dataset from IPFS."""
        
        try:
            content = self.ipfs_client.get(ipfs_hash)
            if not content:
                print(f" Dataset not found: {ipfs_hash}")
                return None
            
            # Handle encryption formats
            if content.startswith("ENCRYPTED:"):
                content = content[10:]
            else:
                # Try AES-GCM envelope (JSON with enc/nonce/ciphertext)
                try:
                    maybe_env = json.loads(content)
                except Exception:
                    maybe_env = None
                if isinstance(maybe_env, dict) and str(maybe_env.get("enc", "")).upper().startswith("AES-GCM"):
                    if not self._enc_enabled:
                        print(" AES-GCM content found but IPFS_ENC_KEY not set; cannot decrypt")
                        return None
                    dec = self._decrypt_envelope(maybe_env)
                    if dec is None:
                        print(" Failed to decrypt AES-GCM content")
                        return None
                    content = dec
            
            # Parse JSON
            dataset_data = json.loads(content)
            
            # Convert back to MedicalDataset
            dataset = MedicalDataset(**dataset_data)
            
            print(f" Downloaded dataset {dataset.dataset_id} from IPFS")
            return dataset
            
        except Exception as e:
            print(f" Failed to download dataset: {e}")
            return None

    def _load_encryption_key(self) -> Optional[bytes]:
        val = env_str("IPFS_ENC_KEY")
        if not val:
            return None
        try:
            key = base64.b64decode(val)
        except Exception:
            return None
        if len(key) not in (16, 24, 32):  # AES-128/192/256
            return None
        return key

    def _encrypt_json(self, plaintext_json: str) -> str:
        if AESGCM is None or self._enc_key is None:
            raise RuntimeError("AESGCM not available or IPFS_ENC_KEY invalid")
        nonce = os.urandom(12)
        aes = AESGCM(self._enc_key)
        ct = aes.encrypt(nonce, plaintext_json.encode(), None)
        env = {
            "v": 1,
            "enc": "AES-GCM",
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ct).decode(),
        }
        return json.dumps(env)

    def _decrypt_envelope(self, env: Dict[str, Any]) -> Optional[str]:
        if AESGCM is None or self._enc_key is None:
            return None
        try:
            nonce_b = base64.b64decode(env.get("nonce", ""))
            ct_b = base64.b64decode(env.get("ciphertext", ""))
            aes = AESGCM(self._enc_key)
            pt = aes.decrypt(nonce_b, ct_b, None)
            return pt.decode()
        except Exception:
            return None
    
    def query_patient_data(self, patient_id: str) -> List[Dict[str, Any]]:
        """Query all data for a specific patient across datasets."""
        
        patient_data = []
        
        # Check all datasets for this patient
        if patient_id in self.patient_mappings:
            for ipfs_hash in self.patient_mappings[patient_id]:
                dataset = self.download_dataset(ipfs_hash)
                if dataset:
                    for record in dataset.patient_records:
                        if record["patient_id"] == patient_id:
                            patient_data.append({
                                "dataset_id": dataset.dataset_id,
                                "ipfs_hash": ipfs_hash,
                                "record": record
                            })
        
        return patient_data
    
    def redact_patient_data(self, patient_id: str, redaction_type: str, reason: str) -> bool:
        """
        Redact patient data from IPFS.
        This implements the "right to be forgotten" by modifying or removing data.
        """
        
        try:
            redaction_id = f"redact_{patient_id}_{int(time.time())}"
            affected_datasets = []
            
            # Find all datasets containing this patient
            if patient_id not in self.patient_mappings:
                print(f" No data found for patient {patient_id}")
                return False
            
            for ipfs_hash in self.patient_mappings[patient_id]:
                dataset = self.download_dataset(ipfs_hash)
                if not dataset:
                    continue
                
                # Find patient record in dataset
                patient_found = False
                for i, record in enumerate(dataset.patient_records):
                    if record["patient_id"] == patient_id:
                        patient_found = True
                        
                        if redaction_type == "DELETE":
                            # Remove patient record completely
                            dataset.patient_records.pop(i)
                            print(f"️  Deleted patient {patient_id} from dataset {dataset.dataset_id}")
                            
                        elif redaction_type == "ANONYMIZE":
                            # Anonymize sensitive fields
                            record["patient_name"] = "[REDACTED]"
                            record["medical_record_number"] = "[REDACTED]"
                            record["date_of_birth"] = "[REDACTED]"
                            record["insurance_id"] = "[REDACTED]"
                            record["emergency_contact"] = "[REDACTED]"
                            print(f" Anonymized patient {patient_id} in dataset {dataset.dataset_id}")
                            
                        elif redaction_type == "MODIFY":
                            # Modify specific fields based on reason
                            if "diagnosis" in reason.lower():
                                record["diagnosis"] = "[MODIFIED]"
                            if "treatment" in reason.lower():
                                record["treatment"] = "[MODIFIED]"
                            print(f"️  Modified patient {patient_id} in dataset {dataset.dataset_id}")
                        
                        break
                
                if patient_found:
                    # Update dataset version and metadata
                    dataset.version = f"{dataset.version}.redacted"
                    dataset.last_updated = int(time.time())
                    
                    # Add redaction record to dataset
                    redaction_record = {
                        "redaction_id": redaction_id,
                        "patient_id": patient_id,
                        "redaction_type": redaction_type,
                        "reason": reason,
                        "timestamp": int(time.time()),
                        "original_ipfs_hash": ipfs_hash
                    }
                    dataset.redaction_log.append(redaction_record)
                    
                    # Remove old version from IPFS
                    self.ipfs_client.rm(ipfs_hash)
                    
                    # Upload new version
                    new_ipfs_hash = self.upload_dataset(dataset)
                    
                    affected_datasets.append({
                        "dataset_id": dataset.dataset_id,
                        "old_hash": ipfs_hash,
                        "new_hash": new_ipfs_hash
                    })
                    
                    # Update mappings
                    if patient_id in self.patient_mappings:
                        self.patient_mappings[patient_id] = [
                            new_ipfs_hash if h == ipfs_hash else h 
                            for h in self.patient_mappings[patient_id]
                        ]
                        
                        # If completely deleted, remove patient mapping
                        if redaction_type == "DELETE":
                            self.patient_mappings[patient_id] = [
                                h for h in self.patient_mappings[patient_id] if h != ipfs_hash
                            ]
                            if not self.patient_mappings[patient_id]:
                                del self.patient_mappings[patient_id]
            
            # Log the redaction operation
            redaction_log_entry = {
                "redaction_id": redaction_id,
                "patient_id": patient_id,
                "redaction_type": redaction_type,
                "reason": reason,
                "timestamp": int(time.time()),
                "affected_datasets": affected_datasets,
                "success": True
            }
            
            self.redaction_log.append(redaction_log_entry)
            
            print(f" Successfully redacted patient {patient_id}")
            print(f"   Type: {redaction_type}")
            print(f"   Affected datasets: {len(affected_datasets)}")
            
            return True
            
        except Exception as e:
            print(f" Failed to redact patient data: {e}")
            return False
    
    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all registered datasets."""
        return list(self.dataset_registry.values())
    
    def get_redaction_history(self, patient_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get redaction history for all patients or a specific patient."""
        
        if patient_id:
            return [r for r in self.redaction_log if r["patient_id"] == patient_id]
        
        return self.redaction_log
    
    def verify_ipfs_integrity(self) -> Dict[str, Any]:
        """Verify integrity of IPFS-stored datasets."""
        
        integrity_report = {
            "total_datasets": len(self.dataset_registry),
            "accessible_datasets": 0,
            "missing_datasets": [],
            "corrupted_datasets": [],
            "verification_timestamp": int(time.time())
        }
        
        for dataset_id, metadata in self.dataset_registry.items():
            ipfs_hash = metadata["ipfs_hash"]
            
            # Check if dataset is accessible
            content = self.ipfs_client.get(ipfs_hash)
            if content:
                integrity_report["accessible_datasets"] += 1
                
                # Basic corruption check (accepts encrypted envelope JSON as valid)
                try:
                    if content.startswith("ENCRYPTED:"):
                        content = content[10:]
                    parsed = json.loads(content)
                    # If envelope, do not attempt to parse inner plaintext here
                    if isinstance(parsed, dict) and "enc" in parsed and "ciphertext" in parsed:
                        pass
                except json.JSONDecodeError:
                    integrity_report["corrupted_datasets"].append({
                        "dataset_id": dataset_id,
                        "ipfs_hash": ipfs_hash,
                        "error": "JSON decode error"
                    })
            else:
                integrity_report["missing_datasets"].append({
                    "dataset_id": dataset_id,
                    "ipfs_hash": ipfs_hash
                })
        
        return integrity_report


# Testing and demonstration
def test_ipfs_medical_data_system():
    """Test the IPFS medical data management system."""
    
    print("\n Testing IPFS Medical Data Management System")
    print("=" * 60)
    
    # Initialize components
    ipfs_client = FakeIPFSClient()
    data_manager = IPFSMedicalDataManager(ipfs_client)
    dataset_generator = MedicalDatasetGenerator()
    
    # Generate sample dataset
    print("\n Generating sample medical dataset...")
    dataset = dataset_generator.generate_dataset(num_patients=50, dataset_name="Emergency Department Records")
    print(f"  Generated dataset with {len(dataset.patient_records)} patients")
    
    # Upload to IPFS
    print("\n Uploading dataset to IPFS...")
    ipfs_hash = data_manager.upload_dataset(dataset, encrypt=True)
    
    # Query specific patient data
    print("\n Querying patient data...")
    sample_patient_id = dataset.patient_records[0]["patient_id"]
    patient_data = data_manager.query_patient_data(sample_patient_id)
    
    if patient_data:
        print(f"  Found data for patient {sample_patient_id}:")
        for data in patient_data:
            print(f"    Dataset: {data['dataset_id']}")
            print(f"    Name: {data['record']['patient_name']}")
            print(f"    Diagnosis: {data['record']['diagnosis']}")
    
    # Test GDPR "Right to be Forgotten"
    print("\n Testing GDPR Right to be Forgotten...")
    test_patient_id = dataset.patient_records[1]["patient_id"]
    original_name = dataset.patient_records[1]["patient_name"]
    
    print(f"  Original patient name: {original_name}")
    
    # Redact patient data
    success = data_manager.redact_patient_data(
        patient_id=test_patient_id,
        redaction_type="ANONYMIZE",
        reason="Patient requested anonymization under GDPR Article 17"
    )
    
    if success:
        # Verify redaction
        redacted_data = data_manager.query_patient_data(test_patient_id)
        if redacted_data:
            redacted_name = redacted_data[0]["record"]["patient_name"]
            print(f"  Redacted patient name: {redacted_name}")
    
    # Test complete deletion
    print("\n️  Testing complete data deletion...")
    delete_patient_id = dataset.patient_records[2]["patient_id"]
    
    data_manager.redact_patient_data(
        patient_id=delete_patient_id,
        redaction_type="DELETE",
        reason="Patient requested complete data deletion"
    )
    
    # Verify deletion
    deleted_data = data_manager.query_patient_data(delete_patient_id)
    if not deleted_data:
        print(f"   Patient {delete_patient_id} data completely deleted")
    else:
        print(f"   Patient {delete_patient_id} data still exists")
    
    # Display redaction history
    print("\n Redaction History:")
    history = data_manager.get_redaction_history()
    for entry in history:
        print(f"  Redaction ID: {entry['redaction_id']}")
        print(f"    Patient: {entry['patient_id']}")
        print(f"    Type: {entry['redaction_type']}")
        print(f"    Reason: {entry['reason']}")
        print(f"    Datasets affected: {len(entry['affected_datasets'])}")
        print()
    
    # Verify IPFS integrity
    print("\n Verifying IPFS integrity...")
    integrity_report = data_manager.verify_ipfs_integrity()
    print(f"  Total datasets: {integrity_report['total_datasets']}")
    print(f"  Accessible: {integrity_report['accessible_datasets']}")
    print(f"  Missing: {len(integrity_report['missing_datasets'])}")
    print(f"  Corrupted: {len(integrity_report['corrupted_datasets'])}")
    
    # List all datasets
    print("\n Dataset Registry:")
    datasets = data_manager.list_datasets()
    for ds in datasets:
        print(f"  {ds['dataset_id']}: {ds['name']}")
        print(f"    IPFS Hash: {ds['ipfs_hash']}")
        print(f"    Patients: {ds['patient_count']}")
        print(f"    Version: {ds['version']}")
        print()
    
    print(" IPFS medical data management test completed!")


if __name__ == "__main__":
    test_ipfs_medical_data_system()  # TODO: check if I completely and correctly check and test all this file (MedicalDataIPFS.py)
    # TODO: Add this test to the tests suite
