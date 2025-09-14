module.exports = {
  // Exclude trivial or test-only contracts from coverage metrics.
  // Paths are relative to Hardhat's sources path (./src).
  skipFiles: [
    'RedactionVerifier.sol',
    'AlwaysFalseVerifier.sol'
  ],
};
