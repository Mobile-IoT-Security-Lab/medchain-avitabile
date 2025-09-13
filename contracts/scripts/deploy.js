// Minimal deploy script that compiles and deploys MedicalDataManager
async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with account:", deployer.address);

  const Factory = await ethers.getContractFactory("MedicalDataManager");
  const contract = await Factory.deploy();
  await contract.deployed();

  console.log("MedicalDataManager deployed at:", contract.address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

