// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title RedactionVerifier (stub)
/// @notice Placeholder verifier that always returns true. Replace with snarkjs-generated verifier later.
contract RedactionVerifier {
    function verifyProof(
        bytes calldata /*proof*/,
        bytes32 /*policyHash*/,
        bytes32 /*merkleRoot*/,
        bytes32 /*originalHash*/,
        bytes32 /*redactedHash*/
    ) external pure returns (bool) {
        return true;
    }
}

