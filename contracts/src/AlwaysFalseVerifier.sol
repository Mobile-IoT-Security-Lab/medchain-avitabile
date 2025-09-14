// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// Test-only verifier that always returns false.
contract AlwaysFalseVerifier {
    function verifyProof(
        bytes calldata,
        bytes32,
        bytes32,
        bytes32,
        bytes32
    ) external pure returns (bool) {
        return false;
    }
}

