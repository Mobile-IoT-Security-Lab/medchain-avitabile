module.exports = {
  // Exclude trivial or test-only contracts from coverage metrics.
  skipFiles: [
    '**/RedactionVerifier.sol',
    '**/AlwaysFalseVerifier.sol'
  ],
};
