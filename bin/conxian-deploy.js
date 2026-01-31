#!/usr/bin/env node
/**
 * Enhanced StacksOrbit CLI with Conxian deployment support
 * Deploy Conxian protocol to testnet with full monitoring
 */

const fs = require("fs");
const path = require("path");
const axios = require("axios");
const { execSync } = require("child_process");
const ConxianDeployer = require("../lib/conxian-deployer");
const Monitor = require("../lib/monitor");
const ConfigManager = require("../lib/config-manager");

async function main() {
  const args = process.argv.slice(2);
  const command = args[0] || "help";

  console.log("🚀 StacksOrbit - Enhanced Conxian Deployment Tool\n");

  switch (command) {
    case "deploy":
      await deployConxian(args.slice(1));
      break;

    case "check":
      await runChecks(args.slice(1));
      break;

    case "monitor":
      await startMonitoring(args.slice(1));
      break;

    case "verify":
      await verifyDeployment(args.slice(1));
      break;

    case "init":
      await initializeConfig(args.slice(1));
      break;

    case "gui":
      await launchGUI(args.slice(1));
      break;

    default:
      showHelp();
  }
}

async function deployConxian(args) {
  console.log("🚀 Starting Conxian deployment...\n");

  // Parse arguments
  const options = parseArgs(args, {
    category: "category",
    batchSize: "batch-size",
    parallel: "parallel",
    dryRun: "dry-run",
    verbose: "verbose",
  });

  try {
    // Load configuration
    const configPath = options.config || ".env";
    const config = await ConfigManager.loadConfig(configPath);
    await ConfigManager.validateConfig(config);

    console.log("📋 Configuration loaded successfully\n");

    // Initialize deployer
    const deployer = new ConxianDeployer({
      network: config.NETWORK || "testnet",
      config: config,
      verbose: options.verbose,
      dryRun: options.dryRun,
      projectRoot: process.cwd(),
    });

    // Execute deployment
    const results = await deployer.deployConxian({
      category: options.category,
      batchSize: parseInt(options.batchSize) || 5,
      parallel: options.parallel,
    });

    if (!options.dryRun) {
      console.log("\n🎉 Deployment completed!");

      if (results.successful.length > 0) {
        console.log("✅ Ready for production verification");
        console.log(
          '💡 Run "stacksorbit monitor" to track deployment confirmation',
        );
      }
    }
  } catch (error) {
    console.error("\n❌ Deployment failed:", error.message);

    if (options.verbose) {
      console.error("Stack trace:", error.stack);
    }

    console.log("\n💡 Troubleshooting tips:");
    console.log("1. Check your .env configuration");
    console.log("2. Ensure sufficient STX balance");
    console.log("3. Verify network connectivity");
    console.log('4. Run "stacksorbit check" for diagnostics');

    process.exit(1);
  }
}

async function runChecks(args) {
  console.log("🔍 Running comprehensive checks...\n");

  const options = parseArgs(args, {
    config: "config",
    verbose: "verbose",
    envOnly: "env-only",
    networkOnly: "network-only",
    compileOnly: "compile-only",
  });

  try {
    const configPath = options.config || ".env";
    const config = await ConfigManager.loadConfig(configPath);
    await ConfigManager.validateConfig(config);

    const deployer = new ConxianDeployer({
      network: config.NETWORK || "testnet",
      config: config,
      verbose: options.verbose,
    });

    let allPassed = true;

    if (options.envOnly || (!options.networkOnly && !options.compileOnly)) {
      console.log("🔧 Environment Check:");
      const envOk = await deployer.checkEnvironment();
      allPassed = allPassed && envOk;
      console.log("");
    }

    if (options.networkOnly || (!options.envOnly && !options.compileOnly)) {
      console.log("🌐 Network Check:");
      const networkOk = await deployer.checkNetwork();
      allPassed = allPassed && networkOk;
      console.log("");
    }

    if (options.compileOnly || (!options.envOnly && !options.networkOnly)) {
      console.log("⚙️  Compilation Check:");
      const compileOk = await deployer.checkCompilation();
      allPassed = allPassed && compileOk;
      console.log("");
    }

    // Always check deployment status
    console.log("📦 Deployment Status:");
    const deploymentInfo = await deployer.checkDeployments();
    console.log(`Mode: ${deploymentInfo.mode.toUpperCase()}`);
    console.log("");

    console.log(
      `${allPassed ? "✅" : "❌"} Overall status: ${allPassed ? "READY" : "ISSUES FOUND"}`,
    );

    if (!allPassed) {
      console.log("\n💡 Fix issues before deployment");
      process.exit(1);
    }
  } catch (error) {
    console.error("\n❌ Check failed:", error.message);
    process.exit(1);
  }
}

async function startMonitoring(args) {
  console.log("📊 Starting deployment monitoring...\n");

  const options = parseArgs(args, {
    config: "config",
    verbose: "verbose",
    follow: "follow",
  });

  try {
    const configPath = options.config || ".env";
    const config = await ConfigManager.loadConfig(configPath);

    const monitor = new Monitor({
      network: config.NETWORK || "testnet",
      verbose: options.verbose,
    });

    // Show API status
    await monitor.checkApiStatus();
    console.log("");

    // Show account info
    await monitor.getAccountInfo(config.SYSTEM_ADDRESS);
    console.log("");

    // Show deployed contracts
    await monitor.getDeployedContracts(config.SYSTEM_ADDRESS);
    console.log("");

    if (options.follow) {
      // Start monitoring deployment progress
      const deployer = new ConxianDeployer({
        network: config.NETWORK || "testnet",
        config: config,
        verbose: options.verbose,
      });

      await deployer.monitorDeploymentProgress();
    }
  } catch (error) {
    console.error("\n❌ Monitoring failed:", error.message);
    process.exit(1);
  }
}

async function verifyDeployment(args) {
  console.log("🔍 Verifying deployment...\n");

  const options = parseArgs(args, {
    config: "config",
    verbose: "verbose",
  });

  try {
    const configPath = options.config || ".env";
    const config = await ConfigManager.loadConfig(configPath);

    const monitor = new Monitor({
      network: config.NETWORK || "testnet",
      verbose: options.verbose,
    });

    // Check API and account
    await monitor.checkApiStatus();
    console.log("");

    const accountInfo = await monitor.getAccountInfo(config.SYSTEM_ADDRESS);
    if (!accountInfo) {
      throw new Error("Could not verify account");
    }
    console.log("");

    // Verify contracts
    const deployedContracts = await monitor.getDeployedContracts(
      config.SYSTEM_ADDRESS,
    );
    console.log("");

    // Check deployment manifest
    const manifestPath = path.join(
      process.cwd(),
      "deployment",
      "testnet-manifest.json",
    );
    if (fs.existsSync(manifestPath)) {
      const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
      console.log("📋 Deployment Manifest:");
      console.log(`   Timestamp: ${manifest.timestamp}`);
      console.log(`   Deployed: ${manifest.deployment.successful.length}`);
      console.log(`   Verified: ${manifest.deployment.verified.length}`);
      console.log(`   Missing: ${manifest.deployment.missing.length}`);
      console.log("");
    }

    console.log("✅ Deployment verification complete");
  } catch (error) {
    console.error("\n❌ Verification failed:", error.message);
    process.exit(1);
  }
}

async function initializeConfig(args) {
  console.log("⚙️  Initializing StacksOrbit configuration...\n");

  const options = parseArgs(args, {
    network: "network",
  });

  try {
    await ConfigManager.initConfig();

    const network = options.network || "testnet";
    console.log(`🔑 Generating ${network} wallet...`);

    const Deployer = require("../lib/deployer");
    const wallet = await Deployer.generateWallet(network);

    console.log("\n✅ Wallet generated:");
    console.log(`   Address: ${wallet.address}`);
    console.log(`   Private Key: ${wallet.privateKey}`);
    console.log(`   Mnemonic: ${wallet.mnemonic}`);

    // Save to config
    await ConfigManager.saveWallet(wallet, network);
    console.log("\n💾 Wallet saved to .env configuration");

    console.log("\n📝 Next steps:");
    console.log("1. Fund the address with STX tokens");
    console.log("2. Review and edit .env file as needed");
    console.log('3. Run "stacksorbit check" to validate setup');
    console.log('4. Run "stacksorbit deploy --dry-run" to test deployment');
  } catch (error) {
    console.error("\n❌ Initialization failed:", error.message);
    process.exit(1);
  }
}

async function launchGUI(args) {
  console.log("🖥️  Launching StacksOrbit GUI...\n");

  const { spawn } = require("child_process");
  const pythonScript = path.join(__dirname, "..", "stacksorbit.py");

  const python = spawn("python", [pythonScript], {
    stdio: "inherit",
    cwd: process.cwd(),
  });

  python.on("error", (err) => {
    console.error("❌ Failed to start GUI:", err.message);
    console.error("Make sure Python 3.8+ is installed and in your PATH");
    process.exit(1);
  });
}

function parseArgs(args, optionMap) {
  const options = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg.startsWith("--")) {
      const optionName = arg.slice(2);
      const mappedName = optionMap[optionName] || optionName;

      if (args[i + 1] && !args[i + 1].startsWith("--")) {
        options[mappedName] = args[i + 1];
        i++; // Skip next arg as it's the value
      } else {
        options[mappedName] = true;
      }
    }
  }

  return options;
}

function showHelp() {
  console.log(`
🚀 StacksOrbit - Enhanced CLI for Conxian Deployment

Usage:
  stacksorbit <command> [options]

Commands:
  deploy          Deploy Conxian contracts to testnet
  check           Run pre-deployment checks
  monitor         Monitor deployment and network status
  verify          Verify deployment success
  init            Initialize configuration and wallet
  gui             Launch GUI interface

Deploy Options:
  --category <name>    Deploy specific category (core, tokens, dex, etc.)
  --batch-size <num>   Number of contracts per batch (default: 5)
  --parallel           Deploy contracts in parallel (experimental)
  --dry-run            Test deployment without executing
  --verbose            Enable detailed logging

Check Options:
  --env-only           Check only environment variables
  --network-only       Check only network connectivity
  --compile-only       Check only contract compilation

Monitor Options:
  --follow             Follow deployment logs
  --api-status         Check Hiro API status

Config Options:
  --network <net>      Network for wallet (testnet, mainnet)

Global Options:
  --config <path>      Path to configuration file (default: .env)
  --verbose            Enable verbose output

Examples:
  stacksorbit init --network testnet
  stacksorbit check --verbose
  stacksorbit deploy --dry-run
  stacksorbit deploy --category core
  stacksorbit deploy --batch-size 10 --parallel
  stacksorbit monitor --follow
  stacksorbit verify

For more information, visit: https://github.com/Anya-org/stacksorbit
`);
}

// Handle uncaught errors
process.on("unhandledRejection", (error) => {
  console.error("❌ Unhandled error:", error);
  process.exit(1);
});

process.on("SIGINT", () => {
  console.log("\n🛑 StacksOrbit stopped by user");
  process.exit(0);
});

// Run the CLI
if (require.main === module) {
  main().catch((error) => {
    console.error("❌ CLI Error:", error.message);
    process.exit(1);
  });
}

module.exports = { main };
