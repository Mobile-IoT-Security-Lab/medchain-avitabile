const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("RedactionVerifier (stub)", function () {
  it("always returns true", async function () {
    const Verifier = await ethers.getContractFactory("RedactionVerifier");
    const verifier = await Verifier.deploy();
    await verifier.waitForDeployment();

    const ok = await verifier.verifyProof(
      "0x",
      ethers.ZeroHash,
      ethers.ZeroHash,
      ethers.ZeroHash,
      ethers.ZeroHash
    );
    expect(ok).to.equal(true);
  });
});

