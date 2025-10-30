require("@nomicfoundation/hardhat-toolbox");
// Enable solidity-coverage plugin
try {
  require("solidity-coverage");
} catch (_) {}

/** @type import('hardhat/config').HardhatUserConfig */
const isCoverage = !!process.env.COVERAGE;
const useViaIR = process.env.NO_VIA_IR !== "1";

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: { enabled: true, runs: 200 },
      // Phase 2 contracts hit stack-too-deep without IR pipeline
      // Allow opt-out via NO_VIA_IR=1 for debugging scenarios
      ...((isCoverage || useViaIR) ? { viaIR: true } : {}),
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
