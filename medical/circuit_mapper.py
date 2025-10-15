"""
Medical Data to Circuit Input Mapper
====================================

This module provides utilities to map medical data records to circom circuit inputs
for zero-knowledge proof generation.

### Bookmark1 for next meeting
"""

import hashlib
import json
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class CircuitInputs:
    """Container for circuit public and private inputs."""
    public_inputs: Dict[str, int]
    private_inputs: Dict[str, Any]


class MedicalDataCircuitMapper:
    """Maps medical data to circom circuit inputs for ZK proof generation."""
    
    @staticmethod
    def hash_to_field_elements(data_str: str, num_elements: int = 4) -> List[int]:
        """
        Convert medical data string to field elements.
        
        Args:
            data_str: String to hash and convert
            num_elements: Number of field elements to produce
            
        Returns:
            List of integers representing field elements
        """
        # Use SHA256 then split into field elements
        h = hashlib.sha256(data_str.encode()).digest()
        elements = []
        bytes_per_element = len(h) // num_elements
        
        for i in range(num_elements):
            chunk = h[i*bytes_per_element:(i+1)*bytes_per_element]
            # Convert bytes to integer (field element)
            # Use modulo to ensure we stay within field bounds
            element = int.from_bytes(chunk, 'big') % (2**250)  # Stay well below BN254 field
            elements.append(element)
        
        return elements
    
    @staticmethod
    def split_256bit_hash(hash_hex: str) -> Tuple[int, int]:
        """
        Split 256-bit hash into two 128-bit limbs.
        
        Args:
            hash_hex: Hexadecimal hash string (with or without 0x prefix)
            
        Returns:
            Tuple of (limb0, limb1) representing lower and upper 128 bits
        """
        # Remove 0x prefix if present
        if hash_hex.startswith('0x'):
            hash_hex = hash_hex[2:]
        
        # Convert to integer
        full_int = int(hash_hex, 16)
        
        # Split into two 128-bit limbs
        limb0 = full_int & ((1 << 128) - 1)  # Lower 128 bits
        limb1 = full_int >> 128  # Upper 128 bits
        
        return limb0, limb1
    
    @staticmethod
    def serialize_medical_data(record_dict: Dict[str, Any]) -> str:
        """
        Serialize medical record to canonical string form.
        
        Args:
            record_dict: Medical record as dictionary
            
        Returns:
            Canonical JSON string
        """
        # Select fields to include in proof
        canonical_fields = {
            "patient_id": record_dict.get("patient_id", ""),
            "diagnosis": record_dict.get("diagnosis", ""),
            "treatment": record_dict.get("treatment", ""),
            "physician": record_dict.get("physician", "")
        }
        return json.dumps(canonical_fields, sort_keys=True)
    
    def apply_redaction(self, original_data: str, redaction_type: str) -> str:
        """
        Apply redaction to data based on type.
        
        Args:
            original_data: Original data string
            redaction_type: Type of redaction (DELETE, MODIFY, ANONYMIZE)
            
        Returns:
            Redacted data string
        """
        try:
            data = json.loads(original_data)
        except json.JSONDecodeError:
            # If not JSON, treat as plain text
            if redaction_type == "DELETE":
                return ""
            elif redaction_type == "ANONYMIZE":
                return "[REDACTED]"
            else:  # MODIFY
                return "[MODIFIED]"
        
        # Apply redaction to JSON data
        if redaction_type == "DELETE":
            return json.dumps({}, sort_keys=True)
        
        elif redaction_type == "ANONYMIZE":
            redacted = {}
            for key, value in data.items():
                if key == "patient_id":
                    redacted[key] = value  # Keep ID for tracking
                else:
                    redacted[key] = "[REDACTED]"
            return json.dumps(redacted, sort_keys=True)
        
        else:  # MODIFY
            redacted = data.copy()
            # Example: anonymize sensitive fields
            if "diagnosis" in redacted:
                redacted["diagnosis"] = "[MODIFIED]"
            if "treatment" in redacted:
                redacted["treatment"] = "[MODIFIED]"
            return json.dumps(redacted, sort_keys=True)
    
    def prepare_circuit_inputs(self, 
                              medical_record_dict: Dict[str, Any],
                              redaction_type: str,
                              policy_hash: str = "default_policy") -> CircuitInputs:
        """
        Prepare all inputs for the redaction circuit.
        
        Args:
            medical_record_dict: Medical record as dictionary
            redaction_type: Type of redaction operation
            policy_hash: Hash of the applicable policy
            
        Returns:
            CircuitInputs object with public and private inputs
        """
        # Serialize original data
        original_data = self.serialize_medical_data(medical_record_dict)
        
        # Apply redaction
        redacted_data = self.apply_redaction(original_data, redaction_type)
        
        # Compute hashes
        original_hash = hashlib.sha256(original_data.encode()).hexdigest()
        redacted_hash = hashlib.sha256(redacted_data.encode()).hexdigest()
        
        # Compute policy hash if not provided
        if policy_hash == "default_policy":
            policy_hash = hashlib.sha256(f"policy_{redaction_type}".encode()).hexdigest()
        elif not policy_hash.startswith('0x'):
            # Hash the policy identifier
            policy_hash = hashlib.sha256(policy_hash.encode()).hexdigest()
        else:
            # Remove 0x prefix
            policy_hash = policy_hash[2:]
        
        # Convert to field elements
        original_elements = self.hash_to_field_elements(original_data, 4)
        redacted_elements = self.hash_to_field_elements(redacted_data, 4)
        policy_elements = self.hash_to_field_elements(policy_hash, 2)
        
        # Split hashes into 128-bit limbs
        orig_h0, orig_h1 = self.split_256bit_hash(original_hash)
        red_h0, red_h1 = self.split_256bit_hash(redacted_hash)
        pol_h0, pol_h1 = self.split_256bit_hash(policy_hash)
        
        # Merkle proof (optional, set enforceMerkle=0 to skip for now)
        # In future, compute actual Merkle path from blockchain state
        merkle_path_elements = [0] * 8
        merkle_path_indices = [0] * 8
        
        # Build public inputs
        public_inputs = {
            "policyHash0": pol_h0,
            "policyHash1": pol_h1,
            "merkleRoot0": 0,  # Set to 0 or compute from blockchain state
            "merkleRoot1": 0,
            "originalHash0": orig_h0,
            "originalHash1": orig_h1,
            "redactedHash0": red_h0,
            "redactedHash1": red_h1,
            "policyAllowed": 1  # 1 = redaction permitted
        }
        
        # Build private inputs
        private_inputs = {
            "originalData": original_elements,
            "redactedData": redacted_elements,
            "policyData": policy_elements,
            "merklePathElements": merkle_path_elements,
            "merklePathIndices": merkle_path_indices,
            "enforceMerkle": 0  # Disable Merkle check for now
        }
        
        return CircuitInputs(
            public_inputs=public_inputs,
            private_inputs=private_inputs
        )
    
    def validate_circuit_inputs(self, inputs: CircuitInputs) -> bool:
        """
        Validate that circuit inputs are properly formatted.
        
        Args:
            inputs: CircuitInputs to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check public inputs
            required_public = [
                "policyHash0", "policyHash1",
                "merkleRoot0", "merkleRoot1",
                "originalHash0", "originalHash1",
                "redactedHash0", "redactedHash1",
                "policyAllowed"
            ]
            
            for key in required_public:
                if key not in inputs.public_inputs:
                    print(f"⚠️  Missing public input: {key}")
                    return False
                if not isinstance(inputs.public_inputs[key], int):
                    print(f"⚠️  Public input {key} must be int, got {type(inputs.public_inputs[key])}")
                    return False
            
            # Check private inputs
            if "originalData" not in inputs.private_inputs:
                print(f"⚠️  Missing private input: originalData")
                return False
            if len(inputs.private_inputs["originalData"]) != 4:
                print(f"⚠️  originalData must have 4 elements")
                return False
            
            if "redactedData" not in inputs.private_inputs:
                print(f"⚠️  Missing private input: redactedData")
                return False
            if len(inputs.private_inputs["redactedData"]) != 4:
                print(f"⚠️  redactedData must have 4 elements")
                return False
            
            if "policyData" not in inputs.private_inputs:
                print(f"⚠️  Missing private input: policyData")
                return False
            if len(inputs.private_inputs["policyData"]) != 2:
                print(f"⚠️  policyData must have 2 elements")
                return False
            
            # Check Merkle inputs
            if "merklePathElements" not in inputs.private_inputs:
                print(f"⚠️  Missing private input: merklePathElements")
                return False
            if len(inputs.private_inputs["merklePathElements"]) != 8:
                print(f"⚠️  merklePathElements must have 8 elements")
                return False
            
            if "merklePathIndices" not in inputs.private_inputs:
                print(f"⚠️  Missing private input: merklePathIndices")
                return False
            if len(inputs.private_inputs["merklePathIndices"]) != 8:
                print(f"⚠️  merklePathIndices must have 8 elements")
                return False
            
            if "enforceMerkle" not in inputs.private_inputs:
                print(f"⚠️  Missing private input: enforceMerkle")
                return False
            
            return True
            
        except Exception as e:
            print(f"⚠️  Validation error: {e}")
            return False

    def _hash_state(self, state_dict: Dict[str, Any]) -> str:
        """
        Compute hash of a state dictionary for consistency proofs.
        
        Args:
            state_dict: State dictionary to hash
            
        Returns:
            Hexadecimal hash string
        """
        # Serialize state to canonical JSON
        state_json = json.dumps(state_dict, sort_keys=True)
        return hashlib.sha256(state_json.encode()).hexdigest()
    
    def prepare_circuit_inputs_with_consistency(
        self,
        medical_record_dict: Dict[str, Any],
        redaction_type: str,
        policy_hash: str = "default_policy",
        consistency_proof=None  # Optional ConsistencyProof
    ) -> CircuitInputs:
        """
        Prepare circuit inputs INCLUDING consistency proof data.
        
        This extends the base circuit inputs with consistency verification:
        - Pre-redaction state hash
        - Post-redaction state hash
        - Consistency check passed flag
        
        Args:
            medical_record_dict: Medical record as dictionary
            redaction_type: Type of redaction operation
            policy_hash: Hash of the applicable policy
            consistency_proof: Optional ConsistencyProof object
            
        Returns:
            CircuitInputs object with public and private inputs including consistency data
        """
        # Get base inputs without consistency
        inputs = self.prepare_circuit_inputs(
            medical_record_dict,
            redaction_type,
            policy_hash
        )
        
        # Add consistency proof data if provided
        if consistency_proof:
            try:
                # Extract state hashes from consistency proof
                pre_state_hash = self._hash_state(
                    consistency_proof.pre_redaction_state
                )
                post_state_hash = self._hash_state(
                    consistency_proof.post_redaction_state
                )
                
                # Split into 128-bit limbs
                pre_h0, pre_h1 = self.split_256bit_hash(pre_state_hash)
                post_h0, post_h1 = self.split_256bit_hash(post_state_hash)
                
                # Add to public inputs
                inputs.public_inputs.update({
                    "preStateHash0": pre_h0,
                    "preStateHash1": pre_h1,
                    "postStateHash0": post_h0,
                    "postStateHash1": post_h1,
                    "consistencyCheckPassed": 1 if consistency_proof.is_valid else 0
                })
                
                print(f"✅ Consistency proof data added to circuit inputs")
                print(f"   Pre-state hash: {pre_state_hash[:16]}...")
                print(f"   Post-state hash: {post_state_hash[:16]}...")
                print(f"   Consistency valid: {consistency_proof.is_valid}")
                
            except Exception as e:
                print(f"⚠️  Failed to add consistency proof data: {e}")
                # Add default values if extraction fails
                inputs.public_inputs.update({
                    "preStateHash0": 0,
                    "preStateHash1": 0,
                    "postStateHash0": 0,
                    "postStateHash1": 0,
                    "consistencyCheckPassed": 0
                })
        else:
            # No consistency proof provided - add defaults
            inputs.public_inputs.update({
                "preStateHash0": 0,
                "preStateHash1": 0,
                "postStateHash0": 0,
                "postStateHash1": 0,
                "consistencyCheckPassed": 0  # Skip consistency check
            })
            print(f"📝 No consistency proof provided, using default values")
        
        return inputs
    
    def validate_circuit_inputs_with_consistency(self, inputs: CircuitInputs) -> bool:
        """
        Validate circuit inputs including consistency proof fields.
        
        Args:
            inputs: CircuitInputs to validate
            
        Returns:
            True if valid, False otherwise
        """
        # First validate base inputs
        if not self.validate_circuit_inputs(inputs):
            return False
        
        # Check consistency-related public inputs (REQUIRED for consistency validation)
        consistency_fields = [
            "preStateHash0", "preStateHash1",
            "postStateHash0", "postStateHash1",
            "consistencyCheckPassed"
        ]
        
        for field in consistency_fields:
            if field not in inputs.public_inputs:
                print(f"⚠️  Missing consistency field: {field}")
                return False
            if not isinstance(inputs.public_inputs[field], int):
                print(f"⚠️  Consistency field {field} must be int, got {type(inputs.public_inputs[field])}")
                return False
        
        return True


# Example usage
if __name__ == "__main__":
    mapper = MedicalDataCircuitMapper()
    
    # Example medical record
    record = {
        "patient_id": "PAT_12345",
        "patient_name": "John Doe",
        "diagnosis": "Hypertension",
        "treatment": "Medication XYZ",
        "physician": "Dr. Smith"
    }
    
    # Prepare circuit inputs
    inputs = mapper.prepare_circuit_inputs(record, "ANONYMIZE")
    
    # Validate
    if mapper.validate_circuit_inputs(inputs):
        print("✅ Circuit inputs are valid")
        print(f"\nPublic inputs: {list(inputs.public_inputs.keys())}")
        print(f"Private inputs: {list(inputs.private_inputs.keys())}")
    else:
        print("❌ Circuit inputs validation failed")
