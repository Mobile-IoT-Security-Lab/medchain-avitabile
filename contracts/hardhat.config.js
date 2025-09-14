require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: { enabled: true, runs: 200 },
    },
  },
  // Our .sol files live in the project root of this Hardhat package
  // (i.e., repo/contracts/*.sol), not in the default ./contracts folder.
  // Configure paths so Hardhat can find and compile them.
  paths: {
    sources: ".",
    tests: "test",
    cache: "cache",
    artifacts: "artifacts",
  },
};
