const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("MedicalDataManager", function () {
  async function deployAll() {
    const [owner, other, approver, outsider] = await ethers.getSigners();
    const Verifier = await ethers.getContractFactory("RedactionVerifier");
    const verifier = await Verifier.deploy();
    await verifier.waitForDeployment();

    const Nullifier = await ethers.getContractFactory("NullifierRegistry");
    const nullifierRegistry = await Nullifier.deploy();
    await nullifierRegistry.waitForDeployment();

    const MDM = await ethers.getContractFactory("MedicalDataManager");
    const mdm = await MDM.deploy(
      ethers.ZeroAddress,
      await nullifierRegistry.getAddress()
    );
    await mdm.waitForDeployment();

    return {
      owner,
      other,
      approver,
      outsider,
      mdm,
      verifier,
      nullifierRegistry,
    };
  }

  it("enforces onlyAuthorized and allows storing data after authorization", async function () {
    const { mdm, owner, other } = await deployAll();

    // other not authorized initially
    await expect(
      mdm
        .connect(other)
        .storeMedicalData("PAT_001", "QmHash", ethers.id("cipher1"))
    ).to.be.revertedWith("Not authorized");

    // Owner authorizes other
    await mdm.connect(owner).setAuthorized(other.address, true);
    await mdm
      .connect(other)
      .storeMedicalData("PAT_001", "QmHash", ethers.id("cipher1"));

    const rec = await mdm.medicalRecords("PAT_001");
    expect(rec.ipfsHash).to.equal("QmHash");
    expect(rec.ciphertextHash).to.equal(ethers.id("cipher1"));
  });

  it("requires proof when requireProofs=true and verifier set; supports proof path", async function () {
    const { mdm, verifier, owner, approver, outsider } = await deployAll();

    // Store a record so redaction makes sense
    await mdm
      .connect(owner)
      .storeMedicalData("PAT_X", "QmData", ethers.id("cipherX"));

    // Outsider is not authorized for setRequireProofs
    await expect(mdm.connect(outsider).setRequireProofs(true)).to.be.revertedWith(
      "Not authorized"
    );

    // Enable proof requirement and set verifier
    await mdm.connect(owner).setRequireProofs(true);
    await mdm.connect(owner).setVerifier(await verifier.getAddress());
    // Use legacy verifier interface for stub
    await mdm.connect(owner).setVerifierType(1);

    // Request without proof must revert
    await expect(
      mdm
        .connect(owner)
        .requestDataRedaction("PAT_X", "DELETE", "gdpr")
    ).to.be.revertedWith("Proof required");

    // With proof succeeds (stub verifier always returns true)
    const zero = ethers.ZeroHash; // bytes32(0)
    await mdm
      .connect(owner)
      .requestDataRedactionWithProof("PAT_X", "DELETE", "gdpr", "0x", zero, zero, zero, zero);

    const reqId = await mdm.nextRequestId();
    expect(Number(reqId)).to.equal(1);

    // Approvals: owner first
    await mdm.connect(owner).approveRedaction(reqId);
    // Duplicate approval by same signer should fail
    await expect(mdm.connect(owner).approveRedaction(reqId)).to.be.revertedWith(
      "Already approved"
    );

    // Authorize another approver and approve
    await mdm.setAuthorized(approver.address, true);
    await mdm.connect(approver).approveRedaction(reqId);

    const req = await mdm.redactionRequests(reqId);
    expect(Number(req.approvals)).to.equal(2);
  });

  it("allows redaction requests without proof when proofs disabled", async function () {
    const { mdm, owner, verifier } = await deployAll();
    // Disable proofs and keep a verifier set
    await mdm.setVerifier(await verifier.getAddress());
    await mdm.setRequireProofs(false);

    // Need an existing record
    await mdm.storeMedicalData("PAT_Y", "QmY", ethers.id("cipherY"));

    await mdm.requestDataRedaction("PAT_Y", "ANONYMIZE", "research");
    const reqId2 = await mdm.nextRequestId();
    expect(Number(reqId2)).to.equal(1);
  });

  it("reverts requestDataRedaction when caller not authorized", async function () {
    const { mdm, outsider } = await deployAll();
    await expect(
      mdm.connect(outsider).requestDataRedaction("PAT_Z", "DELETE", "gdpr")
    ).to.be.revertedWith("Not authorized");
  });

  it("reverts WithProof when requireProofs=true and verifier unset", async function () {
    const { mdm } = await deployAll();
    await mdm.setRequireProofs(true);
    const zero = ethers.ZeroHash;
    await expect(
      mdm.requestDataRedactionWithProof("PAT_Z", "DELETE", "gdpr", "0x", zero, zero, zero, zero)
    ).to.be.revertedWith("Verifier not set");
  });

  it("reverts WithProof when verifier returns false", async function () {
    const { mdm } = await deployAll();
    const FalseV = await ethers.getContractFactory("AlwaysFalseVerifier");
    const fv = await FalseV.deploy();
    await fv.waitForDeployment();
    await mdm.setRequireProofs(true);
    await mdm.setVerifier(await fv.getAddress());
    await mdm.setVerifierType(1);
    const zero = ethers.ZeroHash;
    await expect(
      mdm.requestDataRedactionWithProof("PAT_A", "DELETE", "gdpr", "0x", zero, zero, zero, zero)
    ).to.be.revertedWith("Invalid proof");
  });

  it("allows WithProof when requireProofs=false and verifier unset (skips verification)", async function () {
    const { mdm } = await deployAll();
    await mdm.setRequireProofs(false);
    const zero = ethers.ZeroHash;
    await mdm.requestDataRedactionWithProof("PAT_B", "MODIFY", "policy", "0x", zero, zero, zero, zero);
    const id = await mdm.nextRequestId();
    expect(Number(id)).to.equal(1);
  });

  it("succeeds WithProof when requireProofs=true and verifier returns true", async function () {
    const { mdm } = await deployAll();
    const Verifier = await ethers.getContractFactory("RedactionVerifier");
    const verifier = await Verifier.deploy();
    await verifier.waitForDeployment();
    await mdm.setRequireProofs(true);
    await mdm.setVerifier(await verifier.getAddress());
    await mdm.setVerifierType(1);
    const zero = ethers.ZeroHash;
    await mdm.requestDataRedactionWithProof("PAT_OK", "ANONYMIZE", "policy", "0x", zero, zero, zero, zero);
    const id = await mdm.nextRequestId();
    expect(Number(id)).to.equal(1);
  });

  it("revoking authorization prevents further actions", async function () {
    const { mdm, owner, other } = await deployAll();
    await mdm.connect(owner).setAuthorized(other.address, true);
    await mdm.connect(other).storeMedicalData("PAT_R", "QmR", ethers.id("cipherR"));
    // revoke
    await mdm.connect(owner).setAuthorized(other.address, false);
    await expect(
      mdm.connect(other).storeMedicalData("PAT_R2", "QmR2", ethers.id("cipherR2"))
    ).to.be.revertedWith("Not authorized");
  });

  it("reverts approveRedaction for non-existent request id", async function () {
    const { mdm } = await deployAll();
    await expect(mdm.approveRedaction(12345)).to.be.revertedWith("Request not found");
  });
});
