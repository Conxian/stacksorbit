const { generateWallet } = require('@stacks/wallet-sdk');
const { getAddressFromPrivateKey, TransactionVersion } = require('@stacks/transactions');

const mnemonic = "cute bird surprise boring old news cake design aisle helmet choose tree";

async function main() {
    try {
        const wallet = await generateWallet({ secretKey: mnemonic, password: "password" });
        const account = wallet.accounts[0];
        const address = getAddressFromPrivateKey(account.stxPrivateKey, TransactionVersion.Testnet);
        
        console.log("Mnemonic:", mnemonic);
        console.log("Address:", address);
    } catch (e) {
        console.error(e);
    }
}

main();
