require("@nomicfoundation/hardhat-toolbox");
// Enable solidity-coverage plugin
try {
  require("solidity-coverage");
} catch (_) {}

/** @type import('hardhat/config').HardhatUserConfig */
const isCoverage = !!process.env.COVERAGE;

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: { enabled: true, runs: 200 },
      // solidity-coverage sometimes needs viaIR to avoid stack-too-deep
      ...(isCoverage ? { viaIR: true } : {}),
    },
  },
  // Place Solidity sources under ./src (avoid including node_modules)
  paths: {
    sources: "src",
    tests: "test",
    cache: "cache",
    artifacts: "artifacts",
  },
};
