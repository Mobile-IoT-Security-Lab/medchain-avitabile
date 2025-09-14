// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Minimal Medical Data Manager (scaffold)
/// @notice Stores pointers (IPFS CIDs) and emits events for redaction requests.
///         No PHI on-chain. SNARK verification is deferred to a verifier contract in future steps.
interface IRedactionVerifier {
    function verifyProof(
        bytes calldata proof,
        bytes32 policyHash,
        bytes32 merkleRoot,
        bytes32 originalHash,
        bytes32 redactedHash
    ) external view returns (bool);
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
    }

    mapping(string => MedicalRecordPtr) public medicalRecords; // patientId => record ptr
    mapping(uint256 => RedactionRequestRec) public redactionRequests; // requestId => request
    mapping(uint256 => mapping(address => bool)) public redactionApprovals; // requestId => approver => approved
    mapping(address => bool) public authorizedUsers;            // simplistic ACL (demo)

    uint256 public nextRequestId; // auto-increment id for redaction requests
    address public verifier; // optional verifier; zero address disables proof checks
    bool public requireProofs; // when true and verifier is set, disallow proof-less requests

    modifier onlyAuthorized() {
        require(authorizedUsers[msg.sender], "Not authorized");
        _;
    }

    constructor() {
        authorizedUsers[msg.sender] = true; // deployer is authorized
    }

    function setVerifier(address verifierAddr) external {
        // NOTE: for demo only; in production add access control
        verifier = verifierAddr;
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
            approvals: 0
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
            bool ok = IRedactionVerifier(verifier).verifyProof(
                proof, policyHash, merkleRoot, originalHash, redactedHash
            );
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
            approvals: 0
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
}

