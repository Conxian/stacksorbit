const { makeContractDeploy, broadcastTransaction, AnchorMode } = require('@stacks/transactions');
const { STACKS_MAINNET, STACKS_TESTNET, STACKS_DEVNET } = require('@stacks/network');
const fs = require('fs');

async function deploy(contractName, codeBody, privateKey, networkName) {
  try {
    let network;
    if (networkName.toLowerCase() === 'mainnet') network = STACKS_MAINNET;
    else if (networkName.toLowerCase() === 'devnet') network = STACKS_DEVNET;
    else network = STACKS_TESTNET;
    
    const txOptions = {
      contractName,
      codeBody,
      senderKey: privateKey,
      network,
      anchorMode: AnchorMode.Any,
      postConditionMode: 1, // Allow
    };
    
    const transaction = await makeContractDeploy(txOptions);
    const broadcastResponse = await broadcastTransaction({ transaction, network });
    
    if (broadcastResponse.error) {
      return { success: false, error: broadcastResponse.error, reason: broadcastResponse.reason };
    }
    
    return { success: true, txId: broadcastResponse.txid };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// Check if running from command line
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length < 4) {
    console.error('Usage: node deployer.js <contractName> <path> <privateKey> <network>');
    process.exit(1);
  }
  
  const [contractName, contractPath, privateKey, networkName] = args;
  const codeBody = fs.readFileSync(contractPath, 'utf8');
  
  deploy(contractName, codeBody, privateKey, networkName).then(result => {
    console.log(JSON.stringify(result));
    if (!result.success) process.exit(1);
  });
}

module.exports = { deploy };
