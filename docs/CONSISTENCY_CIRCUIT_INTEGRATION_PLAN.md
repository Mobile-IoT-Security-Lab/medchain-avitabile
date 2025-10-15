# Implementation Guide: Wiring Consistency Proofs into ZK Circuit
<!-- Bookmark1 for next meeting -->

## Current Status Analysis

### What's Already Implemented ✅

1. **Consistency Proof Generation** (`ZK/ProofOfConsistency.py`)
   - `ConsistencyProofGenerator` creates proofs for state transitions
   - Merkle tree verification
   - Hash chain integrity checks
   - Smart contract state consistency

2. **SNARK Circuit** (`circuits/redaction.circom`)
   - H(original) and H(redacted) computation
   - Policy hash matching
   - Optional Merkle inclusion proof
   - Public/private input separation

3. **Medical Redaction Engine** (`medical/MedicalRedactionEngine.py`)
   - Generates both SNARK and consistency proofs
   - Stores consistency proof alongside SNARK proof
   - But: **Consistency proof not wired into circuit inputs**

### What Needs to Be Done 🔄

#### **Task 2a: Wire consistency proofs into circuit public inputs**

Currently, the consistency proof is generated and stored, but its components are not included in the SNARK circuit inputs. We need to:

1. Extract key consistency proof components (Merkle root, state hashes)
2. Add them to circuit public inputs
3. Verify consistency constraints within the circuit
4. Update circuit mapper to handle consistency data

#### **Task 2b: On-chain verification of both SNARK and consistency proofs**

1. Update smart contract to accept consistency proof data
2. Store consistency proof hash on-chain
3. Emit events for consistency verification
4. Create integration tests

## Implementation Plan

### Phase 1: Extend Circuit with Consistency Inputs (2-3 days)

#### Step 1.1: Update Circuit (redaction.circom)

Add consistency-related public inputs:

```circom
// Existing public inputs
signal input policyHash0;
signal input policyHash1;
signal input merkleRoot0;
signal input merkleRoot1;
signal input originalHash0;
signal input originalHash1;
signal input redactedHash0;
signal input redactedHash1;
signal input policyAllowed;

// NEW: Consistency proof inputs
signal input preStateHash0;
signal input preStateHash1;
signal input postStateHash0;
signal input postStateHash1;
signal input consistencyCheckPassed;  // Boolean: 1 if consistency check passed

// Add constraint: consistency must be verified
consistencyCheckPassed === 1;

// Optionally verify state transition hash chain
// preStateHash + operation -> postStateHash verification
```

#### Step 1.2: Update Circuit Mapper

Modify `medical/circuit_mapper.py` to include consistency proof data:

```python
def prepare_circuit_inputs_with_consistency(
    self,
    medical_record_dict: Dict[str, Any],
    redaction_type: str,
    policy_hash: str,
    consistency_proof: Optional[ConsistencyProof] = None
) -> CircuitInputs:
    """Prepare circuit inputs including consistency proof data."""
    
    # Get base inputs
    inputs = self.prepare_circuit_inputs(
        medical_record_dict,
        redaction_type,
        policy_hash
    )
    
    if consistency_proof:
        # Extract state hashes from consistency proof
        pre_state_hash = self._hash_state(
            consistency_proof.pre_redaction_state
        )
        post_state_hash = self._hash_state(
            consistency_proof.post_redaction_state
        )
        
        # Split into limbs
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
    else:
        # Default values if no consistency proof
        inputs.public_inputs.update({
            "preStateHash0": 0,
            "preStateHash1": 0,
            "postStateHash0": 0,
            "postStateHash1": 0,
            "consistencyCheckPassed": 0  # Skip check if not provided
        })
    
    return inputs
```

#### Step 1.3: Update SNARK Manager

Modify `medical/my_snark_manager.py` to pass consistency proof to circuit mapper:

```python
def create_redaction_proof_with_consistency(
    self, 
    redaction_data: Dict[str, Any],
    consistency_proof: Optional[ConsistencyProof] = None
) -> Optional[ZKProof]:
    """Create SNARK proof that includes consistency verification."""
    
    if self.use_real and self.snark_client and self.circuit_mapper:
        try:
            # Extract medical record
            medical_record_dict = self._extract_medical_record_dict(redaction_data)
            redaction_type = redaction_data.get("redaction_type", "MODIFY")
            policy_hash = redaction_data.get("policy_hash", f"policy_{redaction_type}")
            
            # Use circuit mapper WITH consistency proof
            circuit_inputs = self.circuit_mapper.prepare_circuit_inputs_with_consistency(
                medical_record_dict,
                redaction_type,
                policy_hash,
                consistency_proof
            )
            
            # Validate and generate proof...
            # (rest of implementation)
```

### Phase 2: Update Smart Contract (1-2 days)

#### Step 2.1: Modify MedicalDataManager.sol

```solidity
struct RedactionRequest {
    string requestId;
    string patientId;
    string redactionType;
    address requester;
    uint256 timestamp;
    bytes32 zkProofHash;
    bytes32 consistencyProofHash;  // EXISTING
    bytes32 preStateHash;          // NEW
    bytes32 postStateHash;         // NEW
    bool consistencyVerified;      // NEW
    bool executed;
}

function requestDataRedactionWithProofs(
    string memory patientId,
    string memory redactionType,
    string memory reason,
    // SNARK proof components
    uint[2] memory a,
    uint[2][2] memory b,
    uint[2] memory c,
    uint[] memory publicSignals,
    // Consistency proof components
    bytes32 preStateHash,
    bytes32 postStateHash,
    bytes32 consistencyProofHash
) public onlyAuthorized returns (string memory requestId) {
    // Verify SNARK proof (includes consistency check)
    bool valid = verifier.verifyProof(a, b, c, publicSignals);
    require(valid, "Invalid SNARK proof");
    
    // Extract consistency check result from public signals
    // (publicSignals should include consistencyCheckPassed)
    bool consistencyPassed = publicSignals[8] == 1;  // Adjust index
    require(consistencyPassed, "Consistency check failed");
    
    // Create request with consistency data
    RedactionRequest memory req = RedactionRequest({
        requestId: _generateRequestId(),
        patientId: patientId,
        redactionType: redactionType,
        requester: msg.sender,
        timestamp: block.timestamp,
        zkProofHash: keccak256(abi.encodePacked(a, b, c)),
        consistencyProofHash: consistencyProofHash,
        preStateHash: preStateHash,
        postStateHash: postStateHash,
        consistencyVerified: true,
        executed: false
    });
    
    // Store and emit events
    redactionRequests[requestId] = req;
    emit RedactionRequestedWithConsistency(
        requestId,
        patientId,
        consistencyProofHash,
        preStateHash,
        postStateHash
    );
    
    return requestId;
}

event RedactionRequestedWithConsistency(
    string indexed requestId,
    string indexed patientId,
    bytes32 consistencyProofHash,
    bytes32 preStateHash,
    bytes32 postStateHash
);
```

### Phase 3: Integration and Testing (2-3 days)

#### Step 3.1: Update MedicalRedactionEngine

Modify `request_data_redaction` to wire everything together:

```python
def request_data_redaction(
    self,
    patient_id: str,
    redaction_type: str,
    reason: str,
    requester: str,
    requester_role: str = "USER"
) -> Optional[str]:
    """Request redaction with both SNARK and consistency proofs."""
    
    # ... existing code to check patient, policy, etc. ...
    
    # Generate consistency proof FIRST
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
    
    # Generate SNARK proof WITH consistency proof
    zk_proof = self.snark_manager.create_redaction_proof_with_consistency(
        redaction_request_data,
        consistency_proof
    )
    
    # ... rest of implementation ...
```

#### Step 3.2: Create Integration Tests

```python
# tests/test_consistency_circuit_integration.py

def test_consistency_proof_in_circuit():
    """Test that consistency proof is included in SNARK circuit."""
    engine = MyRedactionEngine()
    
    # Create record
    record = engine.create_medical_data_record({
        "patient_id": "CONSISTENCY_TEST_001",
        "diagnosis": "Test diagnosis",
        ...
    })
    engine.store_medical_data(record)
    
    # Request redaction (generates both proofs)
    request_id = engine.request_data_redaction(
        patient_id="CONSISTENCY_TEST_001",
        redaction_type="ANONYMIZE",
        reason="Test consistency integration",
        requester="admin",
        requester_role="ADMIN"
    )
    
    # Verify both proofs exist
    request = engine.redaction_requests[request_id]
    assert request.zk_proof is not None
    assert request.consistency_proof is not None
    assert request.consistency_proof.is_valid
    
    # Verify SNARK proof includes consistency data
    # (Check proof metadata or public signals)
    proof_metadata = engine.snark_manager.get_proof_metadata(request.zk_proof)
    assert "consistency" in proof_metadata

def test_consistency_verification_on_chain():
    """Test on-chain verification of consistency proofs."""
    # Setup EVM backend
    engine = MyRedactionEngine()
    # ... configure EVM client ...
    
    # Submit redaction with proofs
    tx_hash = engine.backend.request_data_redaction(
        patient_id="TEST_001",
        redaction_type="DELETE",
        reason="GDPR",
        proof_payload={
            "zk_proof": {...},
            "consistency_proof": {...}
        }
    )
    
    # Verify event emitted
    events = engine.backend.evm_client.get_events("RedactionRequestedWithConsistency")
    assert len(events) > 0
    assert events[0]["consistencyVerified"] == True
```

## Summary of Changes

### Files to Modify

1. **circuits/redaction.circom**
   - Add consistency-related public inputs (5 new signals)
   - Add consistency verification constraints
   - Recompile circuit

2. **medical/circuit_mapper.py**
   - Add `prepare_circuit_inputs_with_consistency()` method
   - Add `_hash_state()` helper method
   - Update validation

3. **medical/my_snark_manager.py**
   - Add `create_redaction_proof_with_consistency()` method
   - Update existing method to accept consistency proof
   - Update proof metadata

4. **medical/MedicalRedactionEngine.py**
   - Wire consistency proof into SNARK generation
   - Pass consistency proof to snark_manager

5. **contracts/src/MedicalDataManager.sol**
   - Add consistency fields to RedactionRequest struct
   - Update `requestDataRedactionWithProofs()` to accept consistency data
   - Add new event for consistency verification
   - Verify consistency flag in public signals

6. **tests/test_consistency_circuit_integration.py** (new file)
   - Test consistency proof in circuit
   - Test on-chain verification
   - Test end-to-end flow

### Circuit Compilation Steps

After modifying redaction.circom:

```bash
cd circuits
./scripts/compile.sh
PTAU=../tools/pot14_final.ptau ./scripts/setup.sh
./scripts/export-verifier.sh
cd ..
```

### Expected Timeline

- **Week 1**: Circuit updates + circuit mapper (Phase 1)
- **Week 2**: Smart contract updates + EVM integration (Phase 2)
- **Week 3**: Integration testing + documentation (Phase 3)
- **Total**: 2-3 weeks for complete implementation

## Benefits

Once complete, the system will have:

✅ **Cryptographic proof of consistency** embedded in SNARK  
✅ **On-chain verification** of both privacy (SNARK) and integrity (consistency)  
✅ **Unified proof system** - single verification checks both properties  
✅ **Enhanced auditability** - consistency state hashes stored on-chain  
✅ **Production-ready** - complete Avitabile implementation

This completes the "not a simulation" requirement for todo #2!
