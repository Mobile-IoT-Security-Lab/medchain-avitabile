# Zero-Knowledge Proofs Implementation Plan for Data Redaction

## Executive Summary

The codebase already has a **substantial ZK proof infrastructure** in place, but it operates in two modes:

1. **Simulation mode** (default) - using `ZK/SNARKs.py` with cryptographic commitments
2. **Real mode** (when `USE_REAL_SNARK=1`) - using circom circuits and snarkjs via `adapters/snark.py`

**Current Status:**

- ✅ Circom circuit implemented (`circuits/redaction.circom`)
- ✅ SNARK adapter with snarkjs integration (`adapters/snark.py`)
- ✅ Hybrid SNARK manager that switches between real and simulated proofs
- ✅ Integration with medical redaction engine
- ✅ Test infrastructure for both modes
- ⚠️ **Gap: Real SNARK proofs not fully integrated end-to-end**
- ⚠️ **Gap: Circuit inputs need proper data mapping**
- ⚠️ **Gap: On-chain verification not fully connected**

## Architecture Overview

### Current ZK Proof Flow

```text
┌─────────────────────────────────────────────────────────────┐
│                    Medical Redaction Request                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              HybridSNARKManager                              │
│  ┌────────────────────┐      ┌────────────────────┐        │
│  │  Real SNARKs       │      │  Simulated SNARKs  │        │
│  │  (circom/snarkjs)  │ OR   │  (ZK/SNARKs.py)    │        │
│  └────────────────────┘      └────────────────────┘        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    ZKProof Object                            │
│  - proof_id, commitment, nullifier                          │
│  - verifier_challenge, prover_response                      │
│  - merkle_root, timestamp, operation_type                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          Verification (SNARKVerifier)                        │
│  - Nullifier replay check                                   │
│  - Timestamp validation                                     │
│  - Challenge-response verification                          │
│  - Merkle consistency check                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          Redaction Execution (if verified)                   │
└─────────────────────────────────────────────────────────────┘
```

## Key Components Analysis

### 1. Circom Circuit (`circuits/redaction.circom`)

**Capabilities:**

- MiMC-based hashing for field elements
- H(original) and H(redacted) computation
- Policy hash matching
- Merkle inclusion proof (optional, 8-level tree)
- Public/private input separation

**Circuit Inputs:**

```circom
Public inputs:
  - policyHash0, policyHash1 (256-bit split)
  - merkleRoot0, merkleRoot1
  - originalHash0, originalHash1
  - redactedHash0, redactedHash1
  - policyAllowed (boolean flag)

Private inputs:
  - originalData[4] (field elements)
  - redactedData[4]
  - policyData[2]
  - merklePathElements[8]
  - merklePathIndices[8]
  - enforceMerkle (boolean)
```

**Current Limitations:**

- Fixed array sizes (4 for data, 2 for policy)
- MiMC uses zero constants (demo mode)
- No direct mapping from medical records to field elements

### 2. SNARK Adapter (`adapters/snark.py`)

**Capabilities:**

- Wraps snarkjs CLI commands
- Witness generation from JSON inputs
- Groth16 proof generation
- Proof verification off-chain
- Calldata formatting for Solidity
- Full pipeline: `prove_redaction()` method

**Current Status:**

- ✅ All basic operations implemented
- ✅ Error handling and availability checks
- ⚠️ Not actively used in medical redaction flow

### 3. Hybrid SNARK Manager (`medical/MedicalRedactionEngine.py`)

**Design:**

```python
class HybridSNARKManager:
    def __init__(self, snark_client):
        self.snark_client = snark_client
        self.simulation_manager = RedactionSNARKManager()
        self.use_real = snark_client is not None and snark_client.is_enabled()

    def create_redaction_proof(self, redaction_data):
        if self.use_real and self.snark_client:
            # Try real SNARK proof generation
            # Falls back to simulation on failure
        return self.simulation_manager.create_redaction_proof(redaction_data)
```

**Current Gap:**
The real SNARK path in `HybridSNARKManager.create_redaction_proof()` has **placeholder TODOs** for computing proper circuit inputs:

```python
public_inputs = {
    "policyHash0": 0,  # TODO: compute from policy
    "policyHash1": 0,
    "merkleRoot0": 0,  # TODO: compute from state
    "merkleRoot1": 0,
    # ...
}
```

## Priority Implementation Tasks

### Phase 1: Complete Real SNARK Integration (High Priority)

#### Task 1.1: Implement Data-to-Circuit-Input Mapping

**File:** `medical/MedicalRedactionEngine.py`

Create a new helper class:

```python
class MedicalDataCircuitMapper:
    """Maps medical data to circom circuit inputs."""

    @staticmethod
    def hash_to_field_elements(data_str: str, num_elements: int = 4) -> List[int]:
        """Convert medical data string to field elements."""
        # Use SHA256 then split into field elements
        h = hashlib.sha256(data_str.encode()).digest()
        elements = []
        bytes_per_element = len(h) // num_elements
        for i in range(num_elements):
            chunk = h[i*bytes_per_element:(i+1)*bytes_per_element]
            elements.append(int.from_bytes(chunk, 'big'))
        return elements

    @staticmethod
    def split_256bit_hash(hash_hex: str) -> Tuple[int, int]:
        """Split 256-bit hash into two 128-bit limbs."""
        full_int = int(hash_hex, 16)
        limb0 = full_int & ((1 << 128) - 1)
        limb1 = full_int >> 128
        return limb0, limb1

    def prepare_circuit_inputs(self, medical_record: MedicalDataRecord,
                              redaction_type: str,
                              policy_hash: str) -> Dict[str, Any]:
        """Prepare all inputs for the redaction circuit."""
        # Serialize original data
        original_data = json.dumps({
            "patient_id": medical_record.patient_id,
            "diagnosis": medical_record.diagnosis,
            "treatment": medical_record.treatment,
            "physician": medical_record.physician
        }, sort_keys=True)

        # Serialize redacted data
        redacted_data = self._apply_redaction(original_data, redaction_type)

        # Compute hashes
        original_hash = hashlib.sha256(original_data.encode()).hexdigest()
        redacted_hash = hashlib.sha256(redacted_data.encode()).hexdigest()

        # Convert to field elements
        original_elements = self.hash_to_field_elements(original_data, 4)
        redacted_elements = self.hash_to_field_elements(redacted_data, 4)
        policy_elements = self.hash_to_field_elements(policy_hash, 2)

        # Split hashes
        orig_h0, orig_h1 = self.split_256bit_hash(original_hash)
        red_h0, red_h1 = self.split_256bit_hash(redacted_hash)
        pol_h0, pol_h1 = self.split_256bit_hash(policy_hash)

        # Merkle proof (optional, set enforceMerkle=0 to skip)
        merkle_path_elements = [0] * 8
        merkle_path_indices = [0] * 8

        return {
            # Public inputs
            "policyHash0": pol_h0,
            "policyHash1": pol_h1,
            "merkleRoot0": 0,  # Set to 0 or compute from blockchain state
            "merkleRoot1": 0,
            "originalHash0": orig_h0,
            "originalHash1": orig_h1,
            "redactedHash0": red_h0,
            "redactedHash1": red_h1,
            "policyAllowed": 1,

            # Private inputs
            "originalData": original_elements,
            "redactedData": redacted_elements,
            "policyData": policy_elements,
            "merklePathElements": merkle_path_elements,
            "merklePathIndices": merkle_path_indices,
            "enforceMerkle": 0  # Disable Merkle check for now
        }
```

#### Task 1.2: Update HybridSNARKManager to Use Real Circuit

**File:** `medical/MedicalRedactionEngine.py`

```python
class HybridSNARKManager:
    def __init__(self, snark_client=None):
        self.snark_client = snark_client
        self.simulation_manager = RedactionSNARKManager()
        self.circuit_mapper = MedicalDataCircuitMapper()
        self.use_real = snark_client is not None and snark_client.is_enabled()

    def create_redaction_proof(self, redaction_data: Dict[str, Any]) -> Optional[ZKProof]:
        """Create a redaction proof using real snarkjs or simulation."""
        if self.use_real and self.snark_client and self.snark_client.is_available():
            try:
                # Get medical record from redaction data
                original_data = redaction_data.get("original_data", "")
                redacted_data = redaction_data.get("redacted_data", "")
                policy_hash = redaction_data.get("policy_hash", "default_policy")

                # Parse original data JSON to record
                try:
                    record_dict = json.loads(original_data)
                    medical_record = MedicalDataRecord(
                        patient_id=record_dict.get("patient_id", ""),
                        patient_name=record_dict.get("patient_name", ""),
                        medical_record_number=record_dict.get("medical_record_number", ""),
                        diagnosis=record_dict.get("diagnosis", ""),
                        treatment=record_dict.get("treatment", ""),
                        physician=record_dict.get("physician", ""),
                        timestamp=record_dict.get("timestamp", 0),
                        privacy_level=record_dict.get("privacy_level", "PRIVATE"),
                        consent_status=record_dict.get("consent_status", True)
                    )
                except:
                    # Fallback to mock record if parsing fails
                    medical_record = MedicalDataRecord(
                        patient_id="unknown",
                        patient_name="Unknown",
                        medical_record_number="",
                        diagnosis="",
                        treatment="",
                        physician="",
                        timestamp=int(time.time()),
                        privacy_level="PRIVATE",
                        consent_status=True
                    )

                # Prepare circuit inputs
                circuit_inputs = self.circuit_mapper.prepare_circuit_inputs(
                    medical_record,
                    redaction_data.get("redaction_type", "MODIFY"),
                    policy_hash
                )

                # Separate public and private inputs
                public_keys = ["policyHash0", "policyHash1", "merkleRoot0", "merkleRoot1",
                              "originalHash0", "originalHash1", "redactedHash0", "redactedHash1",
                              "policyAllowed"]
                public_inputs = {k: circuit_inputs[k] for k in public_keys if k in circuit_inputs}
                private_inputs = {k: v for k, v in circuit_inputs.items() if k not in public_keys}

                # Generate real SNARK proof
                result = self.snark_client.prove_redaction(public_inputs, private_inputs)

                if result and result.get("verified"):
                    # Convert to ZKProof format
                    calldata = result.get("calldata", {})
                    pub_signals = calldata.get("pubSignals", [])

                    return ZKProof(
                        proof_id=f"real_groth16_{int(time.time())}_{hash(str(pub_signals)) % 10000}",
                        operation_type=redaction_data.get("redaction_type", "MODIFY"),
                        commitment=str(pub_signals[0] if pub_signals else 0),
                        nullifier=f"nullifier_{int(time.time())}",
                        merkle_root=str(public_inputs.get("merkleRoot0", 0)),
                        timestamp=int(time.time()),
                        verifier_challenge=json.dumps(result.get("proof", {})),
                        prover_response=json.dumps(pub_signals)
                    )

            except Exception as e:
                print(f"⚠️  Real SNARK proof generation failed: {e}")
                print(f"   Falling back to simulation mode")

        # Use simulation fallback
        return self.simulation_manager.create_redaction_proof(redaction_data)
```

#### Task 1.3: Add Integration Tests

**File:** `tests/test_real_snark_integration.py` (new file)

```python
"""
Integration tests for real SNARK proof generation and verification.
These tests require:
- circom and snarkjs installed
- Circuit compiled (circuits/build/)
- USE_REAL_SNARK=1 environment variable
"""

import pytest
import os
from medical.MedicalRedactionEngine import MyRedactionEngine, MedicalDataRecord
from adapters.config import env_bool

@pytest.mark.integration
@pytest.mark.skipif(not env_bool("USE_REAL_SNARK", False),
                   reason="Real SNARK mode not enabled")
class TestRealSNARKIntegration:

    def test_real_snark_proof_generation(self):
        """Test real SNARK proof generation with circom circuit."""
        engine = MyRedactionEngine()

        # Create test record
        record = engine.create_medical_data_record({
            "patient_id": "SNARK_TEST_001",
            "patient_name": "Test Patient",
            "diagnosis": "Sensitive diagnosis",
            "treatment": "Sensitive treatment",
            "physician": "Dr. Test",
            "privacy_level": "PRIVATE",
            "consent_status": True
        })

        # Store record
        assert engine.store_medical_data(record)

        # Request redaction with real SNARK proof
        request_id = engine.request_data_redaction(
            patient_id="SNARK_TEST_001",
            redaction_type="ANONYMIZE",
            reason="Test real SNARK proof",
            requester="admin",
            requester_role="ADMIN"
        )

        assert request_id is not None

        # Check proof was generated
        request = engine.redaction_requests[request_id]
        assert request.zk_proof is not None
        assert request.zk_proof.proof_id.startswith("real_groth16_")

        print(f"✅ Real SNARK proof generated: {request.zk_proof.proof_id}")

    def test_real_snark_end_to_end(self):
        """Test complete redaction workflow with real SNARKs."""
        engine = MyRedactionEngine()

        # Create and store record
        record = engine.create_medical_data_record({
            "patient_id": "SNARK_E2E_001",
            "patient_name": "E2E Test",
            "diagnosis": "Original diagnosis",
            "treatment": "Original treatment",
            "physician": "Dr. Original",
            "privacy_level": "PRIVATE",
            "consent_status": True
        })
        engine.store_medical_data(record)

        # Request DELETE with real SNARK
        request_id = engine.request_data_redaction(
            patient_id="SNARK_E2E_001",
            redaction_type="DELETE",
            reason="GDPR erasure with real SNARK",
            requester="regulator",
            requester_role="REGULATOR"
        )

        assert request_id is not None

        # Approve and execute (requires 2 approvals for DELETE)
        assert engine.approve_redaction(request_id, "admin_001", "Approved")
        assert engine.approve_redaction(request_id, "regulator_001", "Approved")

        # Verify deletion
        result = engine.query_medical_data("SNARK_E2E_001", "auditor")
        assert result is None

        print(f"✅ Real SNARK end-to-end test passed")
```

### Phase 2: On-Chain Verification (Medium Priority)

#### Task 2.1: Connect SNARK Verifier to Smart Contract

**Current State:**

- Solidity verifier exists: `contracts/src/RedactionVerifier_groth16.sol`
- Medical contract has placeholder: `contracts/src/MedicalDataManager.sol`
- Need to wire them together

**Implementation:**

1 - Update `MedicalDataManager.sol`:

```solidity
contract MedicalDataManager {
    IRedactionVerifier public verifier;

    constructor(address _verifier) {
        verifier = IRedactionVerifier(_verifier);
    }

    function requestDataRedactionWithProof(
        string memory patientId,
        string memory redactionType,
        string memory reason,
        uint[2] memory a,
        uint[2][2] memory b,
        uint[2] memory c,
        uint[] memory publicSignals
    ) public onlyAuthorized returns (string memory requestId) {
        // Verify SNARK proof on-chain
        bool valid = verifier.verifyProof(a, b, c, publicSignals);
        require(valid, "Invalid SNARK proof");

        // Create redaction request
        // ... existing logic ...
    }
}
```

2 - Update `EVMBackend` in `medical/backends.py` to call this function

#### Task 2.2: Add On-Chain Verification Tests

**File:** `tests/test_onchain_snark_verification.py`

### Phase 3: Enhanced Security Features (Lower Priority)

#### Task 3.1: Implement Nullifier Registry

Prevent proof replay attacks by tracking used nullifiers on-chain.

#### Task 3.2: Add Merkle Tree State Proofs

Currently Merkle verification is optional (`enforceMerkle=0`). Implement proper state tree.

#### Task 3.3: Proof of Consistency Integration

Wire `ConsistencyProofGenerator` output into SNARK public inputs.

## Testing Strategy

### Unit Tests

- ✅ Existing: Simulation mode tests
- ✅ Existing: Adapter interface tests
- 🔄 **Add:** Circuit mapper tests
- 🔄 **Add:** Real vs simulation mode comparison

### Integration Tests

- ✅ Existing: SNARK-EVM basic integration
- 🔄 **Add:** Real circuit end-to-end tests
- 🔄 **Add:** On-chain verification tests
- 🔄 **Add:** Performance benchmarks

### Test Execution

```bash
# Simulation mode (default, no dependencies)
pytest tests/test_snark_system.py

# Real SNARK mode (requires circom/snarkjs)
USE_REAL_SNARK=1 pytest tests/test_real_snark_integration.py -v

# Full integration (requires local blockchain + IPFS)
USE_REAL_SNARK=1 USE_REAL_EVM=1 pytest tests/test_onchain_snark_verification.py -v
```

## Configuration Guide

### .env File Setup

```bash
# Enable real SNARK proofs
USE_REAL_SNARK=1

# Circuit directory (default: circuits)
CIRCUITS_DIR=circuits

# Backend selection
REDACTION_BACKEND=SIMULATED  # or EVM for on-chain

# Optional: EVM integration
USE_REAL_EVM=0
WEB3_PROVIDER_URI=http://127.0.0.1:8545
```

### Prerequisites Check

Before enabling `USE_REAL_SNARK=1`:

1. **Compile circuit:**

   ```bash
   cd circuits
   ./scripts/compile.sh
   ```

2. **Run setup (requires Powers of Tau):**

   ```bash
   PTAU=../tools/pot14_final.ptau ./scripts/setup.sh
   ```

3. **Verify build artifacts exist:**

   ```bash
   ls -la circuits/build/
   # Should see: redaction.wasm, redaction_final.zkey, verification_key.json
   ```

4. **Test proof generation:**

   ```bash
   ./scripts/prove.sh
   ```

## Performance Considerations

### Real SNARK Proofs

- **Proof generation:** ~5-10 seconds (depends on circuit size)
- **Verification:** ~50-100ms off-chain
- **On-chain gas cost:** ~250,000 gas for Groth16 verification

### Simulation Mode

- **Proof generation:** <10ms
- **Verification:** <5ms
- **No gas costs**

**Recommendation:** Use simulation for development/testing, real SNARKs for production.

## Security Notes

1. **Trusted Setup:** Current implementation uses a demo setup. For production, conduct a proper multi-party trusted setup ceremony.

2. **Circuit Audit:** The circuit should be audited before production use. Current version uses:

   - MiMC hash with zero constants (simplified)
   - Fixed-size inputs
   - Optional Merkle proofs

3. **Nullifier Management:** Implement nullifier tracking to prevent replay attacks.

4. **Key Management:** Proving keys and verification keys must be securely stored and versioned.

## Migration Path

### Step 1: Enable Locally (Current Sprint)

- Implement tasks 1.1, 1.2, 1.3
- Test with local circuit
- Verify proof generation works

### Step 2: Integration Testing (Next Sprint)

- Deploy to local test network
- Test on-chain verification
- Performance benchmarking

### Step 3: Staging Deployment (Future)

- Conduct trusted setup
- Deploy to testnet
- Security audit

### Step 4: Production (Future)

- Production trusted setup ceremony
- Deploy to mainnet
- Monitoring and alerting

## Success Metrics

- ✅ **Phase 1 Complete:** Real SNARK proofs generate successfully in medical redaction flow
- ✅ **Phase 2 Complete:** On-chain verification passes for valid proofs
- ✅ **Phase 3 Complete:** Zero replay attacks, nullifier tracking working
- ✅ **Production Ready:** <2s proof generation, <100k gas verification, circuit audited

## References

- **Circom Documentation:** <https://docs.circom.io/>
- **snarkjs Guide:** <https://github.com/iden3/snarkjs>
- **Groth16 Paper:** <https://eprint.iacr.org/2016/260.pdf>
- **MiMC Hash:** <https://eprint.iacr.org/2016/492.pdf>

## Next Steps

1. **Immediate:** Implement `MedicalDataCircuitMapper` class (Task 1.1)
2. **This Week:** Update `HybridSNARKManager` to use real circuit (Task 1.2)
3. **Next Week:** Add integration tests (Task 1.3)
4. **Following Sprint:** Begin Phase 2 (on-chain verification)
