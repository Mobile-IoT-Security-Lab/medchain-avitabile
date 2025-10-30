// Minimal deploy script that compiles and deploys MedicalDataManager,
// then writes deployed addresses to contracts/deployments/<chainId>/.
const fs = require('fs');
const path = require('path');
const hre = require('hardhat');

async function getAddressCompat(contract) {
  // ethers v6 exposes getAddress()/target; v5 uses .address
  if (typeof contract.getAddress === 'function') {
    return await contract.getAddress();
  }
  if (contract.address) return contract.address;
  if (contract.target) return contract.target;
  return '';
}

async function waitDeployedCompat(contract) {
  // ethers v6: waitForDeployment(); v5: deployed()
  if (typeof contract.waitForDeployment === 'function') {
    await contract.waitForDeployment();
  } else if (typeof contract.deployed === 'function') {
    await contract.deployed();
  }
}

// Minimal deploy script that compiles and deploys MedicalDataManager
async function main() {
  // Ensure compile has run
  await hre.run('compile');

  const { ethers } = hre;
  const [deployer] = await ethers.getSigners();
  const deployerAddr = deployer.address || (deployer.getAddress && await deployer.getAddress());
  console.log('Deploying with account:', deployerAddr);

  // Deploy dependencies first
  const NullifierFactory = await ethers.getContractFactory('NullifierRegistry');
  const nullifier = await NullifierFactory.deploy();
  await waitDeployedCompat(nullifier);
  const nullifierAddr = await getAddressCompat(nullifier);
  console.log('NullifierRegistry deployed at:', nullifierAddr);

  // Deploy Groth16 verifier (snarkjs-generated alias)
  const VerifierFactory = await ethers.getContractFactory('RedactionVerifierG16');
  const verifier = await VerifierFactory.deploy();
  await waitDeployedCompat(verifier);
  const verifierAddr = await getAddressCompat(verifier);
  console.log('RedactionVerifier (Groth16) deployed at:', verifierAddr);

  // Deploy MedicalDataManager wired to verifier + nullifier registry
  const Factory = await ethers.getContractFactory('MedicalDataManager');
  const contract = await Factory.deploy(verifierAddr, nullifierAddr);
  await waitDeployedCompat(contract);

  // Set verifier type explicitly to Groth16 (enum value 2)
  try {
    const tx2 = await contract.setVerifierType(2);
    await tx2.wait();
  } catch (e) {
    console.warn('setVerifierType failed (non-fatal):', e && e.message ? e.message : e);
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

  const managerAddr = await getAddressCompat(contract);
  console.log('MedicalDataManager deployed at:', managerAddr);
  console.log('chainId:', chainId, 'blockNumber:', blockNumber);

  // Write per-chain deployment files
  const deploymentsDir = path.join(__dirname, '..', 'deployments', chainId);
  fs.mkdirSync(deploymentsDir, { recursive: true });
  const managerOut = {
    address: managerAddr,
    chainId: chainId,
    blockNumber: blockNumber || 0,
  };
  const nullifierOut = {
    address: nullifierAddr,
    chainId: chainId,
    blockNumber: blockNumber || 0,
  };
  const verifierOut = {
    address: verifierAddr,
    chainId: chainId,
    blockNumber: blockNumber || 0,
  };
  fs.writeFileSync(path.join(deploymentsDir, 'MedicalDataManager.json'), JSON.stringify(managerOut, null, 2));
  fs.writeFileSync(path.join(deploymentsDir, 'NullifierRegistry.json'), JSON.stringify(nullifierOut, null, 2));
  fs.writeFileSync(path.join(deploymentsDir, 'RedactionVerifier.json'), JSON.stringify(verifierOut, null, 2));

  // Write consolidated addresses file at contracts root
  const rootFile = path.join(__dirname, '..', 'deployed_addresses.json');
  let consolidated = {};
  try {
    consolidated = JSON.parse(fs.readFileSync(rootFile, 'utf8'));
  } catch {}
  consolidated['MedicalDataManager'] = managerOut;
  consolidated['NullifierRegistry'] = nullifierOut;
  consolidated['RedactionVerifier'] = verifierOut;
  fs.writeFileSync(rootFile, JSON.stringify(consolidated, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
