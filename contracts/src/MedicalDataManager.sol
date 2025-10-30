// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Medical Data Manager with Phase 2 On-Chain Verification
/// @notice Stores pointers (IPFS CIDs) and emits events for redaction requests.
///         No PHI on-chain. Full SNARK + consistency proof verification with nullifier tracking.
/// @dev Bookmark2 for next meeting - Phase 2 on-chain verification implementation
interface IRedactionVerifier {
    function verifyProof(
        bytes calldata proof,
        bytes32 policyHash,
        bytes32 merkleRoot,
        bytes32 originalHash,
        bytes32 redactedHash
    ) external view returns (bool);
}

/// @notice Groth16 verifier interface exported by snarkjs
interface IGroth16Verifier {
    function verifyProof(
        uint[2] calldata _pA,
        uint[2][2] calldata _pB,
        uint[2] calldata _pC,
        uint[1] calldata _pubSignals
    ) external view returns (bool);
}

/// @notice Nullifier registry interface for replay prevention
interface INullifierRegistry {
    function isNullifierValid(bytes32 nullifier) external view returns (bool);
    function recordNullifier(bytes32 nullifier) external returns (bool);
    function getNullifierInfo(bytes32 nullifier) external view returns (uint256 timestamp, address submitter);
}

contract MedicalDataManager {
    event DataStored(string indexed patientId, string ipfsHash, bytes32 ciphertextHash, uint256 timestamp);
    event RedactionRequested(
        uint256 indexed requestId,
        string indexed patientId,
        string redactionType,
        string reason,
        address requester,
        uint256 timestamp
    );
    event RedactionApproved(uint256 indexed requestId, address indexed approver, uint256 approvals, uint256 timestamp);
    event ProofVerificationSucceeded(uint256 indexed requestId, string verifierType, uint256 timestamp);
    event ProofVerificationFailed(uint256 indexed requestId, string verifierType, string reason, uint256 timestamp);
    event ProofVerifiedOnChain(
        uint256 indexed requestId,
        bytes32 indexed nullifier,
        bytes32 zkProofHash,
        bytes32 consistencyProofHash,
        uint256 timestamp
    );
    event NullifierRecorded(uint256 indexed requestId, bytes32 indexed nullifier);
    event ConsistencyProofStored(
        uint256 indexed requestId,
        bytes32 consistencyProofHash,
        bytes32 preStateHash,
        bytes32 postStateHash
    );

    struct MedicalRecordPtr {
        string ipfsHash;        // CID of encrypted/censored data
        bytes32 ciphertextHash; // SHA-256 over stored payload (e.g., AES-GCM envelope)
        uint256 lastUpdated;    // last update timestamp
    }

    struct RedactionRequestRec {
        string patientId;
        string redactionType;
        string reason;
        address requester;
        uint256 timestamp;
        bool executed;
        uint256 approvals;
        bytes32 zkProofHash;           // Hash of the SNARK proof
        bytes32 consistencyProofHash;  // Hash of consistency proof
        bytes32 nullifier;             // Nullifier for replay prevention
        bytes32 preStateHash;          // Pre-redaction state hash
        bytes32 postStateHash;         // Post-redaction state hash
    }

    mapping(string => MedicalRecordPtr) public medicalRecords; // patientId => record ptr
    mapping(uint256 => RedactionRequestRec) public redactionRequests; // requestId => request
    mapping(uint256 => mapping(address => bool)) public redactionApprovals; // requestId => approver => approved
    mapping(address => bool) public authorizedUsers;            // simplistic ACL (demo)

    uint256 public nextRequestId; // auto-increment id for redaction requests
    address public verifier; // optional verifier; zero address disables proof checks
    bool public requireProofs; // when true and verifier is set, disallow proof-less requests

    enum VerifierType { None, Legacy, Groth16 }
    VerifierType public verifierType; // select which verifier ABI to use
    
    INullifierRegistry public nullifierRegistry;  // for replay prevention

    modifier onlyAuthorized() {
        require(authorizedUsers[msg.sender], "Not authorized");
        _;
    }
    
    /// @notice Constructor with nullifier registry (Phase 2)
    /// @param _verifier Address of the Groth16 verifier contract
    /// @param _nullifierRegistry Address of the nullifier registry contract
    constructor(address _verifier, address _nullifierRegistry) {
        verifier = _verifier;
        nullifierRegistry = INullifierRegistry(_nullifierRegistry);
        verifierType = VerifierType.Groth16;
        requireProofs = (_verifier != address(0));
        authorizedUsers[msg.sender] = true;
    }

    function setVerifier(address verifierAddr) external {
        // NOTE: for demo only; in production add access control
        verifier = verifierAddr;
    }
    
    function setNullifierRegistry(address _nullifierRegistry) external onlyAuthorized {
        nullifierRegistry = INullifierRegistry(_nullifierRegistry);
    }

    function setVerifierType(uint8 mode) external {
        // NOTE: for demo only; in production add access control
        require(mode <= uint8(VerifierType.Groth16), "invalid mode");
        verifierType = VerifierType(mode);
    }

    function setRequireProofs(bool value) external {
        // NOTE: for demo only; in production add access control
        require(authorizedUsers[msg.sender], "Not authorized");
        requireProofs = value;
    }

    function setAuthorized(address user, bool enabled) external {
        // NOTE: for demo only; in production add access control
        authorizedUsers[user] = enabled;
    }

    function storeMedicalData(
        string calldata patientId,
        string calldata ipfsHash,
        bytes32 ciphertextHash
    ) external onlyAuthorized {
        medicalRecords[patientId] = MedicalRecordPtr({
            ipfsHash: ipfsHash,
            ciphertextHash: ciphertextHash,
            lastUpdated: block.timestamp
        });
        emit DataStored(patientId, ipfsHash, ciphertextHash, block.timestamp);
    }

    function requestDataRedaction(
        string calldata patientId,
        string calldata redactionType,
        string calldata reason
    ) external onlyAuthorized {
        // If global proof requirement is enabled and a verifier is configured, reject proof-less requests
        require(!(requireProofs && verifier != address(0)), "Proof required");
        uint256 reqId = ++nextRequestId;
        redactionRequests[reqId] = RedactionRequestRec({
            patientId: patientId,
            redactionType: redactionType,
            reason: reason,
            requester: msg.sender,
            timestamp: block.timestamp,
            executed: false,
            approvals: 0,
            zkProofHash: bytes32(0),
            consistencyProofHash: bytes32(0),
            nullifier: bytes32(0),
            preStateHash: bytes32(0),
            postStateHash: bytes32(0)
        });
        emit RedactionRequested(reqId, patientId, redactionType, reason, msg.sender, block.timestamp);
    }

    function requestDataRedactionWithProof(
        string calldata patientId,
        string calldata redactionType,
        string calldata reason,
        bytes calldata proof,
        bytes32 policyHash,
        bytes32 merkleRoot,
        bytes32 originalHash,
        bytes32 redactedHash
    ) external onlyAuthorized {
        if (requireProofs) {
            require(verifier != address(0), "Verifier not set");
        }
        if (verifier != address(0)) {
            require(verifierType == VerifierType.Legacy, "verifier type mismatch");
            bool ok = IRedactionVerifier(verifier).verifyProof(
                proof, policyHash, merkleRoot, originalHash, redactedHash
            );
            if (ok) {
                emit ProofVerificationSucceeded(nextRequestId + 1, "Legacy", block.timestamp);
            } else {
                emit ProofVerificationFailed(nextRequestId + 1, "Legacy", "Invalid proof", block.timestamp);
            }
            require(ok, "Invalid proof");
        }
        uint256 reqId = ++nextRequestId;
        redactionRequests[reqId] = RedactionRequestRec({
            patientId: patientId,
            redactionType: redactionType,
            reason: reason,
            requester: msg.sender,
            timestamp: block.timestamp,
            executed: false,
            approvals: 0,
            zkProofHash: keccak256(abi.encodePacked(proof, policyHash, merkleRoot, originalHash, redactedHash)),
            consistencyProofHash: bytes32(0),
            nullifier: bytes32(0),
            preStateHash: originalHash,
            postStateHash: redactedHash
        });
        emit RedactionRequested(reqId, patientId, redactionType, reason, msg.sender, block.timestamp);
    }

    function requestDataRedactionWithGroth16Proof(
        string calldata patientId,
        string calldata redactionType,
        string calldata reason,
        uint[2] calldata pA,
        uint[2][2] calldata pB,
        uint[2] calldata pC,
        uint[1] calldata pubSignals
    ) external onlyAuthorized {
        if (requireProofs) {
            require(verifier != address(0), "Verifier not set");
        }
        if (verifier != address(0)) {
            require(verifierType == VerifierType.Groth16, "verifier type mismatch");
            bool ok = IGroth16Verifier(verifier).verifyProof(pA, pB, pC, pubSignals);
            if (ok) {
                emit ProofVerificationSucceeded(nextRequestId + 1, "Groth16", block.timestamp);
            } else {
                emit ProofVerificationFailed(nextRequestId + 1, "Groth16", "Invalid proof", block.timestamp);
            }
            require(ok, "Invalid proof");
        }
        uint256 reqId = ++nextRequestId;
        redactionRequests[reqId] = RedactionRequestRec({
            patientId: patientId,
            redactionType: redactionType,
            reason: reason,
            requester: msg.sender,
            timestamp: block.timestamp,
            executed: false,
            approvals: 0,
            zkProofHash: keccak256(abi.encodePacked(pA, pB, pC, pubSignals)),
            consistencyProofHash: bytes32(0),
            nullifier: bytes32(0),
            preStateHash: bytes32(0),
            postStateHash: bytes32(0)
        });
        emit RedactionRequested(reqId, patientId, redactionType, reason, msg.sender, block.timestamp);
    }

    function approveRedaction(uint256 requestId) external onlyAuthorized {
        require(redactionRequests[requestId].timestamp != 0, "Request not found");
        require(!redactionApprovals[requestId][msg.sender], "Already approved");
        redactionApprovals[requestId][msg.sender] = true;
        redactionRequests[requestId].approvals += 1;
        emit RedactionApproved(requestId, msg.sender, redactionRequests[requestId].approvals, block.timestamp);
    }
    
    /// @notice Request data redaction with full Phase 2 verification (SNARK + consistency + nullifier)
    /// @param patientId The patient identifier
    /// @param redactionType Type of redaction (DELETE, ANONYMIZE, MODIFY)
    /// @param reason Reason for redaction
    /// @param pA Groth16 proof component A
    /// @param pB Groth16 proof component B
    /// @param pC Groth16 proof component C
    /// @param pubSignals Public signals for the proof
    /// @param nullifier Unique nullifier to prevent replay attacks
    /// @param consistencyProofHash Hash of the consistency proof
    /// @param preStateHash Hash of pre-redaction state
    /// @param postStateHash Hash of post-redaction state
    /// @return requestId The created request ID
    function requestDataRedactionWithFullProofs(
        string calldata patientId,
        string calldata redactionType,
        string calldata reason,
        uint[2] calldata pA,
        uint[2][2] calldata pB,
        uint[2] calldata pC,
        uint[1] calldata pubSignals,
        bytes32 nullifier,
        bytes32 consistencyProofHash,
        bytes32 preStateHash,
        bytes32 postStateHash
    ) external onlyAuthorized returns (uint256 requestId) {
        // Phase 2 Step 1: Check nullifier validity (prevent replay attacks)
        if (address(nullifierRegistry) != address(0)) {
            require(
                nullifierRegistry.isNullifierValid(nullifier),
                "Nullifier already used (replay attack prevented)"
            );
        }
        
        // Phase 2 Step 2: Verify SNARK proof on-chain
        if (verifier != address(0) && requireProofs) {
            require(verifierType == VerifierType.Groth16, "Verifier type mismatch");
            bool proofValid = IGroth16Verifier(verifier).verifyProof(pA, pB, pC, pubSignals);
            if (proofValid) {
                emit ProofVerificationSucceeded(nextRequestId + 1, "Groth16", block.timestamp);
            } else {
                emit ProofVerificationFailed(nextRequestId + 1, "Groth16", "Invalid proof", block.timestamp);
                revert("Invalid SNARK proof");
            }
        }
        
        // Phase 2 Step 3: Record nullifier (prevent future replays)
        if (address(nullifierRegistry) != address(0)) {
            bool nullifierRecorded = nullifierRegistry.recordNullifier(nullifier);
            require(nullifierRecorded, "Failed to record nullifier");
            emit NullifierRecorded(nextRequestId + 1, nullifier);
        }
        
        // Phase 2 Step 4: Create enhanced redaction request with all proof data
        requestId = ++nextRequestId;
        
        bytes32 zkProofHash = keccak256(abi.encodePacked(pA, pB, pC, pubSignals));
        
        redactionRequests[requestId] = RedactionRequestRec({
            patientId: patientId,
            redactionType: redactionType,
            reason: reason,
            requester: msg.sender,
            timestamp: block.timestamp,
            executed: false,
            approvals: 0,
            zkProofHash: zkProofHash,
            consistencyProofHash: consistencyProofHash,
            nullifier: nullifier,
            preStateHash: preStateHash,
            postStateHash: postStateHash
        });
        
        // Phase 2 Step 5: Emit comprehensive events for audit trail
        emit RedactionRequested(
            requestId,
            patientId,
            redactionType,
            reason,
            msg.sender,
            block.timestamp
        );
        
        emit ProofVerifiedOnChain(
            requestId,
            nullifier,
            zkProofHash,
            consistencyProofHash,
            block.timestamp
        );
        
        emit ConsistencyProofStored(
            requestId,
            consistencyProofHash,
            preStateHash,
            postStateHash
        );
        
        return requestId;
    }
    
    /// @notice Get full proof details for a redaction request (Phase 2)
    /// @param requestId The request ID to query
    /// @return zkProofHash Hash of the SNARK proof
    /// @return consistencyProofHash Hash of the consistency proof
    /// @return nullifier The nullifier used
    /// @return preStateHash Pre-redaction state hash
    /// @return postStateHash Post-redaction state hash
    function getRedactionProofDetails(uint256 requestId) 
        external 
        view 
        returns (
            bytes32 zkProofHash,
            bytes32 consistencyProofHash,
            bytes32 nullifier,
            bytes32 preStateHash,
            bytes32 postStateHash
        ) 
    {
        RedactionRequestRec memory req = redactionRequests[requestId];
        return (
            req.zkProofHash,
            req.consistencyProofHash,
            req.nullifier,
            req.preStateHash,
            req.postStateHash
        );
    }
    
    /// @notice Check if a nullifier has been used (Phase 2)
    /// @param nullifier The nullifier to check
    /// @return True if nullifier is valid (unused)
    function isNullifierValid(bytes32 nullifier) external view returns (bool) {
        if (address(nullifierRegistry) == address(0)) {
            return true; // No registry configured, all nullifiers valid
        }
        return nullifierRegistry.isNullifierValid(nullifier);
    }
}
