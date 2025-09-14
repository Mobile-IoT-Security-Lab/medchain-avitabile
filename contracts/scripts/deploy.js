// Minimal deploy script that compiles and deploys MedicalDataManager,
// then writes deployed addresses to contracts/deployments/<chainId>/.
const fs = require('fs');
const path = require('path');

// Minimal deploy script that compiles and deploys MedicalDataManager
async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with account:", deployer.address);

  const Factory = await ethers.getContractFactory("MedicalDataManager");
  const contract = await Factory.deploy();
  await contract.deployed();

  // Optional: deploy verifier and set it
  const VerifierFactory = await ethers.getContractFactory("RedactionVerifier");
  const verifier = await VerifierFactory.deploy();
  await verifier.deployed();
  try {
    const tx = await contract.setVerifier(verifier.address);
    await tx.wait();
  } catch (e) {
    console.warn("setVerifier failed (non-fatal):", e.message || e);
  }

  // Network metadata
  const net = await deployer.provider.getNetwork();
  const chainId = net.chainId?.toString() || String(net.chainId);
  let blockNumber;
  try {
    const r = (contract.deployTransaction && contract.deployTransaction.wait)
      ? await contract.deployTransaction.wait()
      : (contract.deploymentTransaction && (await contract.deploymentTransaction().wait()));
    blockNumber = r && r.blockNumber;
  } catch (e) {
    blockNumber = await deployer.provider.getBlockNumber();
  }

  console.log("MedicalDataManager deployed at:", contract.address);
  console.log("RedactionVerifier deployed at:", verifier.address);
  console.log("chainId:", chainId, "blockNumber:", blockNumber);

  // Write per-chain deployment files
  const deploymentsDir = path.join(__dirname, '..', 'deployments', chainId);
  fs.mkdirSync(deploymentsDir, { recursive: true });
  const managerOut = {
    address: contract.address,
    chainId: chainId,
    blockNumber: blockNumber || 0,
  };
  const verifierOut = {
    address: verifier.address,
    chainId: chainId,
    blockNumber: blockNumber || 0,
  };
  fs.writeFileSync(path.join(deploymentsDir, 'MedicalDataManager.json'), JSON.stringify(managerOut, null, 2));
  fs.writeFileSync(path.join(deploymentsDir, 'RedactionVerifier.json'), JSON.stringify(verifierOut, null, 2));

  // Write consolidated addresses file at contracts root
  const rootFile = path.join(__dirname, '..', 'deployed_addresses.json');
  let consolidated = {};
  try {
    consolidated = JSON.parse(fs.readFileSync(rootFile, 'utf8'));
  } catch {}
  consolidated['MedicalDataManager'] = managerOut;
  consolidated['RedactionVerifier'] = verifierOut;
  fs.writeFileSync(rootFile, JSON.stringify(consolidated, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
