
import os

code = r'''const fs = require('fs');
const path = require('path');
const Deployer = require('./deployer');
const ConfigManager = require('./config-manager');

// Assuming these might be needed, or we implement manual nonce fetch
// const { getAddressFromPrivateKey } = require('@stacks/transactions');

class ConxianDeployer extends Deployer {
  constructor(options = {}) {
    super(options);
    this.projectRoot = options.projectRoot || process.cwd();
    this.contractPaths = this._loadClarinetPaths();
    this.contractCategories = {}; 
  }

  _loadClarinetPaths() {
    const clarinetPath = path.join(this.projectRoot, 'Clarinet.toml');
    const map = {};
    if (fs.existsSync(clarinetPath)) {
        const content = fs.readFileSync(clarinetPath, 'utf8');
        const regex = /^\[contracts\.([a-zA-Z0-9_-]+)\][\s\S]*?path\s*=\s*[\"'](.*?)[\"']/gm;
        let match;
        while ((match = regex.exec(content)) !== null) {
            const name = match[1];
            let relativePath = match[2];
            relativePath = relativePath.replace(/\\/g, '/'); 
            map[name] = relativePath;
        }
    }
    return map;
  }

  async deployConxian(options = {}) {
    console.log('📋 Analyzing Conxian contracts...');
    
    // Get account info for nonce - implementing simple fetch since we lack easy access to Deployer's internal helpers
    let nonce = 0;
    try {
        const apiUrl = this.config.CORE_API_URL || 'https://api.testnet.hiro.so';
        const addr = this.config.SYSTEM_ADDRESS;
        // Using built-in fetch (Node 18+) or axios if available from require
        // We imported axios in deployer.js usually. Let's see if we can use it.
        // But axios is not imported here. Let's assume fetch is available (Node 22 is used).
        console.log(`fetching nonce for ${addr}...`);
        const resp = await fetch(`${apiUrl}/v2/accounts/${addr}?proof=0`);
        if (resp.ok) {
            const data = await resp.json();
            nonce = data.nonce;
            console.log(`📊 Current Nonce: ${nonce}`);
        } else {
             console.log(`Non-200 response for nonce: ${resp.status}`);
        }
    } catch (e) {
        console.error('⚠️ Failed to fetch nonce, assuming 0', e.message);
    }
    
    const deploymentInfo = {
        nonce: nonce,
        mode: 'upgrade'
    };

    const contractsToDeploy = Object.keys(this.contractPaths);
    
    if (contractsToDeploy.length === 0) {
        console.log('⚠️  No contracts found in Clarinet.toml');
        return { successful: [], failed: [] };
    }
    
    const results = { successful: [], failed: [], skipped: [] };
    
    console.log(`🚀 Deploying ${contractsToDeploy.length} contracts...`);
    
    // We need to pass 'results' because deploySingleContract modifies it?
    // Based on output, it takes results.
    
    for (const name of contractsToDeploy) {
        try {
            const relPath = this.contractPaths[name];
            const fullPath = path.join(this.projectRoot, relPath);
            
            // console.log(`📄 Deploying ${name}...`);
            
            const contractObj = { name: name, path: fullPath };
            
            // Calling the correct method signature found in log
            await this.deploySingleContract(contractObj, results, deploymentInfo);
            
        } catch (e) {
            console.error(`❌ Error loop ${name}: ${e.message}`);
            results.failed.push({name, error: e.message});
        }
    }
    
    return results;
  }
}

module.exports = ConxianDeployer;
'''

with open('lib/conxian-deployer.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated lib/conxian-deployer.js with deploySingleContract usage")
