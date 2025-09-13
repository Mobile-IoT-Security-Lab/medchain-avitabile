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
    event DataStored(string indexed patientId, string ipfsHash, uint256 timestamp);
    event RedactionRequested(
        string indexed patientId,
        string redactionType,
        string reason,
        address requester,
        uint256 timestamp
    );

    struct MedicalRecordPtr {
        string ipfsHash;        // CID of encrypted/censored data
        uint256 lastUpdated;    // last update timestamp
    }

    mapping(string => MedicalRecordPtr) public medicalRecords; // patientId => record ptr
    mapping(address => bool) public authorizedUsers;            // simplistic ACL (demo)

    address public verifier; // optional verifier; zero address disables proof checks

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

    function setAuthorized(address user, bool enabled) external {
        // NOTE: for demo only; in production add access control
        authorizedUsers[user] = enabled;
    }

    function storeMedicalData(
        string calldata patientId,
        string calldata ipfsHash
    ) external onlyAuthorized {
        medicalRecords[patientId] = MedicalRecordPtr({
            ipfsHash: ipfsHash,
            lastUpdated: block.timestamp
        });
        emit DataStored(patientId, ipfsHash, block.timestamp);
    }

    function requestDataRedaction(
        string calldata patientId,
        string calldata redactionType,
        string calldata reason
    ) external onlyAuthorized {
        emit RedactionRequested(patientId, redactionType, reason, msg.sender, block.timestamp);
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
        if (verifier != address(0)) {
            bool ok = IRedactionVerifier(verifier).verifyProof(
                proof, policyHash, merkleRoot, originalHash, redactedHash
            );
            require(ok, "Invalid proof");
        }
        emit RedactionRequested(patientId, redactionType, reason, msg.sender, block.timestamp);
    }
}
