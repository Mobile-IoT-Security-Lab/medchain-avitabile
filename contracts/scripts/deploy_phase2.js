// Phase 2 Contract Deployment Script
// Bookmark2 for next meeting - Phase 2 on-chain verification implementation

const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
   console.log("🚀 Deploying Phase 2 contracts...\n");

   const [deployer] = await hre.ethers.getSigners();
   console.log(`📝 Deploying with account: ${deployer.address}`);
   console.log(
      `💰 Account balance: ${(
         await deployer.provider.getBalance(deployer.address)
      ).toString()}\n`
   );

   // Step 1: Deploy NullifierRegistry
   console.log("📦 Deploying NullifierRegistry...");
   const NullifierRegistry = await hre.ethers.getContractFactory(
      "NullifierRegistry"
   );
   const nullifierRegistry = await NullifierRegistry.deploy();
   await nullifierRegistry.waitForDeployment();
   const nullifierAddr = await nullifierRegistry.getAddress();
   console.log(`✅ NullifierRegistry deployed at: ${nullifierAddr}\n`);

   // Step 2: Deploy Groth16 Verifier
   console.log("📦 Deploying RedactionVerifier_groth16...");
   const Verifier = await hre.ethers.getContractFactory(
      "RedactionVerifier_groth16"
   );
   const verifier = await Verifier.deploy();
   await verifier.waitForDeployment();
   const verifierAddr = await verifier.getAddress();
   console.log(`✅ RedactionVerifier_groth16 deployed at: ${verifierAddr}\n`);

   // Step 3: Deploy MedicalDataManager with references
   console.log("📦 Deploying MedicalDataManager...");
   const MedicalDataManager = await hre.ethers.getContractFactory(
      "MedicalDataManager"
   );
   const medicalManager = await MedicalDataManager.deploy(
      verifierAddr,
      nullifierAddr
   );
   await medicalManager.waitForDeployment();
   const medicalAddr = await medicalManager.getAddress();
   console.log(`✅ MedicalDataManager deployed at: ${medicalAddr}\n`);

   // Step 4: Verify deployment configuration
   console.log("🔍 Verifying deployment configuration...");
   const registeredNullifier = await medicalManager.nullifierRegistry();
   const registeredVerifier = await medicalManager.verifier();
   console.log(`   Nullifier Registry: ${registeredNullifier}`);
   console.log(`   Verifier: ${registeredVerifier}`);
   console.log(`   Proofs Required: ${await medicalManager.requireProofs()}`);
   console.log(`   Verifier Type: ${await medicalManager.verifierType()}\n`);

   // Step 5: Save deployment addresses
   const addresses = {
      NullifierRegistry: {
         address: nullifierAddr,
         deployedAt: new Date().toISOString(),
         deployer: deployer.address,
         network: hre.network.name,
         chainId: (await hre.ethers.provider.getNetwork()).chainId.toString(),
      },
      RedactionVerifier_groth16: {
         address: verifierAddr,
         deployedAt: new Date().toISOString(),
         deployer: deployer.address,
         network: hre.network.name,
         chainId: (await hre.ethers.provider.getNetwork()).chainId.toString(),
      },
      MedicalDataManager: {
         address: medicalAddr,
         deployedAt: new Date().toISOString(),
         deployer: deployer.address,
         network: hre.network.name,
         chainId: (await hre.ethers.provider.getNetwork()).chainId.toString(),
         configuration: {
            nullifierRegistry: nullifierAddr,
            verifier: verifierAddr,
            requireProofs: true,
         },
      },
   };

   const outputPath = path.join(__dirname, "../deployed_addresses.json");
   fs.writeFileSync(outputPath, JSON.stringify(addresses, null, 2));
   console.log(`💾 Deployment addresses saved to: ${outputPath}\n`);

   // Step 6: Export environment variables template
   const envTemplate = `# Phase 2 Deployment Configuration
# Generated: ${new Date().toISOString()}

# EVM Configuration
USE_REAL_EVM=1
WEB3_PROVIDER_URI=http://127.0.0.1:8545
EVM_CHAIN_ID=${(await hre.ethers.provider.getNetwork()).chainId}
EVM_PRIVATE_KEY=<YOUR_PRIVATE_KEY>

# Contract Addresses
NULLIFIER_REGISTRY_ADDRESS=${nullifierAddr}
VERIFIER_ADDRESS=${verifierAddr}
MEDICAL_CONTRACT_ADDRESS=${medicalAddr}

# Backend Configuration
REDACTION_BACKEND=EVM

# Circuit Configuration
CIRCUITS_DIR=circuits
`;

   const envPath = path.join(__dirname, "../.env.phase2");
   fs.writeFileSync(envPath, envTemplate);
   console.log(`📝 Environment template saved to: ${envPath}\n`);

   // Step 7: Summary
   console.log("=" * 60);
   console.log("✅ Phase 2 Deployment Complete!");
   console.log("=" * 60);
   console.log("\n📋 Deployment Summary:");
   console.log(`   Network: ${hre.network.name}`);
   console.log(
      `   Chain ID: ${(await hre.ethers.provider.getNetwork()).chainId}`
   );
   console.log(`   Deployer: ${deployer.address}`);
   console.log(`\n📦 Deployed Contracts:`);
   console.log(`   NullifierRegistry: ${nullifierAddr}`);
   console.log(`   RedactionVerifier: ${verifierAddr}`);
   console.log(`   MedicalDataManager: ${medicalAddr}`);
   console.log(`\n🔧 Next Steps:`);
   console.log(`   1. Update .env with values from .env.phase2`);
   console.log(
      `   2. Run integration tests: pytest tests/test_phase2_onchain_verification.py`
   );
   console.log(
      `   3. Verify contracts on block explorer (if using testnet/mainnet)`
   );
   console.log(`   4. Test nullifier prevention and consistency proofs`);
   console.log("\n");
}

main()
   .then(() => process.exit(0))
   .catch((error) => {
      console.error(error);
      process.exit(1);
   });
