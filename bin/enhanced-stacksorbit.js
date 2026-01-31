#!/usr/bin/env node
/**
 * Enhanced StacksOrbit CLI for Conxian Deployment
 * Full-featured deployment tool with Hiro API integration
 */

const { spawn } = require("child_process");
const path = require("path");

function main() {
  const args = process.argv.slice(2);
  const command = args[0] || "help";

  console.log("🚀 StacksOrbit - Enhanced Conxian Deployment Tool\n");

  // Handle Node.js CLI commands
  if (command === "deploy") {
    console.log("📦 Running enhanced deployment...\n");
    runPythonScript("enhanced_conxian_deployment.py", args.slice(1));
  } else if (command === "monitor") {
    console.log("📊 Running deployment monitoring...\n");
    runPythonScript("deployment_monitor.py", args.slice(1));
  } else if (command === "verify") {
    console.log("🔍 Running deployment verification...\n");
    runPythonScript("deployment_verifier.py", args.slice(1));
  } else if (command === "check") {
    console.log("🔍 Running pre-deployment checks...\n");
    runPythonScript("conxian_testnet_deploy.py", ["check", ...args.slice(1)]);
  } else if (command === "detect") {
    console.log("🔍 Running enhanced auto-detection...\n");
    runPythonScript("stacksorbit_auto_detect.py", args.slice(1));
  } else if (command === "gui") {
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
  } else {
    showHelp();
  }
}

function runPythonScript(scriptName, args = []) {
  const scriptDir = path.join(__dirname, "..");
  const pythonScript = path.join(scriptDir, scriptName);

  const pythonArgs = [pythonScript, ...args];
  const python = spawn("python", pythonArgs, {
    stdio: "inherit",
    cwd: process.cwd(),
  });

  python.on("error", (err) => {
    console.error(`❌ Failed to run ${scriptName}:`, err.message);
    console.error(
      "Make sure Python 3.8+ and required dependencies are installed",
    );
    console.error("Run: pip install -r requirements.txt");
    process.exit(1);
  });

  python.on("exit", (code) => {
    process.exit(code);
  });
}

function showHelp() {
  console.log(`
🚀 StacksOrbit - Enhanced CLI for Conxian Deployment

Usage:
  stacksorbit <command> [options]

Commands:
  deploy          Deploy Conxian contracts to testnet
  detect          Run enhanced auto-detection
  check           Run pre-deployment checks
  monitor         Monitor deployment and network status
  verify          Verify deployment success
  gui             Launch GUI interface

Enhanced Features:
  ✅ Full CLI with command-line arguments
  ✅ Hiro API integration for monitoring
  ✅ Comprehensive deployment verification
  ✅ Real-time deployment tracking
  ✅ Configuration management
  ✅ Batch deployment with dependency ordering
  ✅ Gas estimation and optimization
  ✅ Deployment manifest generation
  ✅ Network health monitoring

Quick Start:
  1. Detect:      stacksorbit detect
  2. Initialize: stacksorbit check
  3. Deploy:     stacksorbit deploy --dry-run
  4. Monitor:    stacksorbit monitor --follow
  5. Verify:     stacksorbit verify

For detailed help, run the Python scripts directly:
  python enhanced_conxian_deployment.py --help
  python deployment_monitor.py --help
  python deployment_verifier.py --help

For more information, visit: https://github.com/Anya-org/stacksorbit
`);
}

if (require.main === module) {
  main();
}

module.exports = { main };
