#!/usr/bin/env node
/**
 * StacksOrbit CLI - Professional deployment tool for Stacks blockchain
 * Enhanced CLI with full deployment and monitoring capabilities
 */

const { Command } = require("commander");
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");
const axios = require("axios");

// Import deployment modules
const Deployer = require("../lib/deployer");
const ConfigManager = require("../lib/config-manager");
const Monitor = require("../lib/monitor");

const program = new Command();

// CLI configuration
program
  .name("stacksorbit")
  .description(
    "Professional deployment tool for Stacks blockchain smart contracts",
  )
  .version("1.2.0");

// Global options
program
  .option("-v, --verbose", "enable verbose output")
  .option("--config <path>", "path to configuration file", ".env")
  .option(
    "--network <network>",
    "target network (devnet, testnet, mainnet)",
    "testnet",
  )
  .option("--dry-run", "perform dry run without actual deployment");

// Deploy command
program
  .command("deploy")
  .description("Deploy contracts to Stacks network")
  .option(
    "-f, --filter <contracts>",
    "comma-separated list of contracts to deploy",
  )
  .option("-m, --mode <mode>", "deployment mode (full, upgrade)", "full")
  .option(
    "--batch-size <size>",
    "number of contracts to deploy in each batch",
    "10",
  )
  .option("--skip-compile", "skip compilation check")
  .option("--parallel", "deploy contracts in parallel (experimental)")
  .action(async (options) => {
    try {
      console.log("🚀 StacksOrbit - Starting deployment...\n");

      // Load configuration
      const config = await ConfigManager.loadConfig(program.opts().config);
      if (program.opts().verbose) {
        console.log("📋 Configuration loaded:", config);
      }

      // Initialize deployer
      const deployer = new Deployer({
        network: program.opts().network,
        config: config,
        verbose: program.opts().verbose,
        dryRun: program.opts().dryRun,
      });

      // Run pre-deployment checks
      console.log("🔍 Running pre-deployment checks...");
      const checksPassed = await deployer.runPreChecks();
      if (!checksPassed && !program.opts().dryRun) {
        console.error(
          "❌ Pre-deployment checks failed. Use --dry-run to continue anyway.",
        );
        process.exit(1);
      }

      // Get deployment list
      const contracts = await deployer.getDeploymentList(options.filter);
      console.log(`📦 Found ${contracts.length} contracts to deploy`);

      if (program.opts().dryRun) {
        console.log("🔍 DRY RUN - No actual deployment will occur");
        console.log("📋 Contracts that would be deployed:");
        contracts.forEach((contract) => console.log(`  - ${contract.name}`));
        return;
      }

      // Execute deployment
      console.log("\n🚀 Starting deployment...");
      const results = await deployer.deployContracts(contracts, {
        mode: options.mode,
        batchSize: parseInt(options.batchSize),
        parallel: options.parallel,
      });

      // Show results
      console.log("\n📊 Deployment Results:");
      console.log(`✅ Successful: ${results.successful.length}`);
      console.log(`❌ Failed: ${results.failed.length}`);
      console.log(`⏭️  Skipped: ${results.skipped.length}`);

      if (results.failed.length > 0) {
        console.log("\n❌ Failed contracts:");
        results.failed.forEach((contract) => {
          console.log(`  - ${contract.name}: ${contract.error}`);
        });
        process.exit(1);
      }

      console.log("\n🎉 Deployment completed successfully!");
    } catch (error) {
      console.error("❌ Deployment failed:", error.message);
      if (program.opts().verbose) {
        console.error(error.stack);
      }
      process.exit(1);
    }
  });

// Pre-check command
program
  .command("check")
  .description("Run pre-deployment checks")
  .option("--env-only", "check only environment variables")
  .option("--network-only", "check only network connectivity")
  .option("--compile-only", "check only contract compilation")
  .option("--deployment-only", "check only existing deployments")
  .action(async (options) => {
    try {
      console.log("🔍 StacksOrbit - Running pre-deployment checks...\n");

      const config = await ConfigManager.loadConfig(program.opts().config);
      const deployer = new Deployer({
        network: program.opts().network,
        config: config,
        verbose: program.opts().verbose,
      });

      let allPassed = true;

      if (
        options.envOnly ||
        (!options.networkOnly &&
          !options.compileOnly &&
          !options.deploymentOnly)
      ) {
        console.log("🔧 Checking environment variables...");
        const envOk = await deployer.checkEnvironment();
        allPassed = allPassed && envOk;
      }

      if (
        options.networkOnly ||
        (!options.envOnly && !options.compileOnly && !options.deploymentOnly)
      ) {
        console.log("🌐 Checking network connectivity...");
        const networkOk = await deployer.checkNetwork();
        allPassed = allPassed && networkOk;
      }

      if (
        options.compileOnly ||
        (!options.envOnly && !options.networkOnly && !options.deploymentOnly)
      ) {
        console.log("⚙️  Checking contract compilation...");
        const compileOk = await deployer.checkCompilation();
        allPassed = allPassed && compileOk;
      }

      if (
        options.deploymentOnly ||
        (!options.envOnly && !options.networkOnly && !options.compileOnly)
      ) {
        console.log("📦 Checking existing deployments...");
        const deploymentOk = await deployer.checkDeployments();
        console.log(`Deployment mode: ${deploymentOk.mode}`);
      }

      console.log(
        `\n${allPassed ? "✅" : "❌"} All checks ${allPassed ? "passed" : "failed"}`,
      );
    } catch (error) {
      console.error("❌ Check failed:", error.message);
      process.exit(1);
    }
  });

// Monitor command
program
  .command("monitor")
  .description("Monitor deployment and network status")
  .option("-f, --follow", "follow deployment progress")
  .option("-t, --tail <lines>", "number of log lines to show", "50")
  .option("--api-status", "check Hiro API status")
  .action(async (options) => {
    try {
      console.log("📊 StacksOrbit - Monitoring deployment...\n");

      const monitor = new Monitor({
        network: program.opts().network,
        verbose: program.opts().verbose,
      });

      if (options.apiStatus) {
        console.log("🌐 Checking Hiro API status...");
        const apiStatus = await monitor.checkApiStatus();
        console.log(`API Status: ${apiStatus.status}`);
        console.log(`Block Height: ${apiStatus.blockHeight}`);
        console.log(`Network: ${apiStatus.network}`);
      }

      if (options.follow) {
        console.log("🔄 Following deployment logs...");
        await monitor.followLogs(options.tail);
      }
    } catch (error) {
      console.error("❌ Monitoring failed:", error.message);
      process.exit(1);
    }
  });

// Config command
program
  .command("config")
  .description("Manage configuration")
  .addCommand(
    new Command("init")
      .description("Initialize configuration file")
      .action(async () => {
        try {
          console.log("⚙️  Initializing StacksOrbit configuration...\n");
          await ConfigManager.initConfig();
          console.log("✅ Configuration initialized successfully");
          console.log("📝 Edit .env file with your deployment settings");
        } catch (error) {
          console.error("❌ Configuration init failed:", error.message);
          process.exit(1);
        }
      }),
  )
  .addCommand(
    new Command("validate")
      .description("Validate configuration file")
      .action(async () => {
        try {
          console.log("🔍 Validating configuration...\n");
          const config = await ConfigManager.loadConfig(program.opts().config);
          const isValid = await ConfigManager.validateConfig(config);
          console.log(
            `${isValid ? "✅" : "❌"} Configuration is ${isValid ? "valid" : "invalid"}`,
          );
        } catch (error) {
          console.error("❌ Configuration validation failed:", error.message);
          process.exit(1);
        }
      }),
  );

// Wallet command
program
  .command("wallet")
  .description("Wallet management")
  .addCommand(
    new Command("generate")
      .description("Generate new wallet")
      .option(
        "-n, --network <network>",
        "network for wallet (testnet, mainnet)",
        "testnet",
      )
      .option("--save", "save wallet to config file")
      .action(async (options) => {
        try {
          console.log(`🔑 Generating ${options.network} wallet...\n`);
          const wallet = await Deployer.generateWallet(options.network);

          console.log("✅ Wallet generated:");
          console.log(`Address: ${wallet.address}`);
          console.log(`Private Key: ${wallet.privateKey}`);
          console.log(`Mnemonic: ${wallet.mnemonic}`);

          if (options.save) {
            await ConfigManager.saveWallet(wallet, options.network);
            console.log("💾 Wallet saved to configuration");
          }
        } catch (error) {
          console.error("❌ Wallet generation failed:", error.message);
          process.exit(1);
        }
      }),
  );

// GUI command (fallback to original functionality)
program
  .command("gui")
  .description("Launch GUI interface")
  .action(() => {
    console.log("🖥️  Launching StacksOrbit GUI...\n");

    const scriptDir = path.join(__dirname, "..");
    const pythonScript = path.join(scriptDir, "stacksorbit.py");

    const python = spawn("python", [pythonScript], {
      stdio: "inherit",
      cwd: process.cwd(),
    });

    python.on("error", (err) => {
      console.error("❌ Failed to start GUI:", err.message);
      console.error("Make sure Python 3.8+ is installed and in your PATH");
      process.exit(1);
    });
  });

// Default action - show help if no command specified
program.action(() => {
  if (program.args.length === 0) {
    program.help();
  }
});

// Parse command line arguments
program.parse();

// Handle uncaught errors
process.on("unhandledRejection", (error) => {
  console.error("❌ Unhandled error:", error);
  process.exit(1);
});

process.on("SIGINT", () => {
  console.log("\n🛑 StacksOrbit stopped by user");
  process.exit(0);
});
