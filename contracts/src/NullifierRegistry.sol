// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Nullifier Registry for SNARK Proof Replay Prevention
/// @notice Tracks used nullifiers to prevent proof replay attacks in the Avitabile redactable blockchain
/// @dev Bookmark2 for next meeting - Phase 2 on-chain verification implementation
contract NullifierRegistry {
    // Nullifier → timestamp mapping
    mapping(bytes32 => uint256) public usedNullifiers;
    
    // Optional: Track nullifier by user for auditing
    mapping(bytes32 => address) public nullifierSubmitter;
    
    // Events
    event NullifierRecorded(bytes32 indexed nullifier, address indexed submitter, uint256 timestamp);
    event NullifierCheckFailed(bytes32 indexed nullifier, uint256 previousTimestamp, address originalSubmitter);
    event NullifierBatchRecorded(uint256 count, uint256 timestamp);
    
    // Admin (for demo; use AccessControl in production)
    address public admin;
    bool public paused;
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can call this function");
        _;
    }
    
    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }
    
    constructor() {
        admin = msg.sender;
        paused = false;
    }
    
    /// @notice Check if a nullifier has been used
    /// @param nullifier The nullifier to check
    /// @return True if nullifier is unused (valid), false if already used
    function isNullifierValid(bytes32 nullifier) external view returns (bool) {
        return usedNullifiers[nullifier] == 0;
    }
    
    /// @notice Record a new nullifier (called by authorized contracts)
    /// @param nullifier The nullifier to record
    /// @return True if successfully recorded, false if already exists
    function recordNullifier(bytes32 nullifier) external whenNotPaused returns (bool) {
        if (usedNullifiers[nullifier] != 0) {
            emit NullifierCheckFailed(
                nullifier, 
                usedNullifiers[nullifier],
                nullifierSubmitter[nullifier]
            );
            return false;
        }
        
        usedNullifiers[nullifier] = block.timestamp;
        nullifierSubmitter[nullifier] = msg.sender;
        
        emit NullifierRecorded(nullifier, msg.sender, block.timestamp);
        return true;
    }
    
    /// @notice Get timestamp when nullifier was used
    /// @param nullifier The nullifier to query
    /// @return timestamp Timestamp (0 if not used)
    /// @return submitter Address that submitted the nullifier
    function getNullifierInfo(bytes32 nullifier) 
        external 
        view 
        returns (uint256 timestamp, address submitter) 
    {
        return (usedNullifiers[nullifier], nullifierSubmitter[nullifier]);
    }
    
    /// @notice Batch check multiple nullifiers
    /// @param nullifiers Array of nullifiers to check
    /// @return Array of booleans (true = valid/unused)
    function areNullifiersValid(bytes32[] calldata nullifiers) 
        external 
        view 
        returns (bool[] memory) 
    {
        bool[] memory results = new bool[](nullifiers.length);
        for (uint i = 0; i < nullifiers.length; i++) {
            results[i] = (usedNullifiers[nullifiers[i]] == 0);
        }
        return results;
    }
    
    /// @notice Batch record multiple nullifiers (gas optimization)
    /// @param nullifiers Array of nullifiers to record
    /// @return successCount Number of nullifiers successfully recorded
    function recordNullifierBatch(bytes32[] calldata nullifiers) 
        external 
        whenNotPaused 
        returns (uint256 successCount) 
    {
        successCount = 0;
        for (uint i = 0; i < nullifiers.length; i++) {
            if (usedNullifiers[nullifiers[i]] == 0) {
                usedNullifiers[nullifiers[i]] = block.timestamp;
                nullifierSubmitter[nullifiers[i]] = msg.sender;
                emit NullifierRecorded(nullifiers[i], msg.sender, block.timestamp);
                successCount++;
            } else {
                emit NullifierCheckFailed(
                    nullifiers[i],
                    usedNullifiers[nullifiers[i]],
                    nullifierSubmitter[nullifiers[i]]
                );
            }
        }
        emit NullifierBatchRecorded(successCount, block.timestamp);
        return successCount;
    }
    
    /// @notice Emergency pause (admin only)
    function pause() external onlyAdmin {
        paused = true;
    }
    
    /// @notice Unpause (admin only)
    function unpause() external onlyAdmin {
        paused = false;
    }
    
    /// @notice Transfer admin role (admin only)
    /// @param newAdmin Address of new admin
    function transferAdmin(address newAdmin) external onlyAdmin {
        require(newAdmin != address(0), "Invalid admin address");
        admin = newAdmin;
    }
}
