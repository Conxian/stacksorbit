# StacksOrbit Agent Instructions

Welcome to StacksOrbit! This document provides a comprehensive guide for developers and AI agents working on this project. It is the "single source of truth" for all development and deployment information.

## 1. Project Overview

StacksOrbit is an advanced deployment tool for the Stacks blockchain. It provides a full-featured command-line interface (CLI), integration with the Hiro API, comprehensive monitoring, and support for chainhooks. The goal of this project is to provide a user-friendly and powerful tool for deploying smart contracts to the Stacks blockchain with confidence.

### 1.1. Architectural Overview

StacksOrbit is a modular, command-line-driven tool for deploying and managing Stacks-based smart contracts. The following diagram illustrates the high-level architecture of the system:

```graph
[ User ] -> [ CLI (`stacksorbit_cli.py`) ] -> [ Core Deployer ] -> [ Stacks Blockchain ]
   |                                              ^
   |                                              |
   +-----> [ Monitoring Dashboard ] <-------------+
```

* **User:** The developer or operator interacting with the tool.
* **CLI (`stacksorbit_cli.py`):** The primary entry point for all commands. It parses user input and delegates tasks to the appropriate modules.
* **Core Deployer:** The heart of the system, responsible for orchestrating the deployment process.
* **Monitoring Dashboard:** A separate process that provides a real-time view of the deployment and network status.
* **Stacks Blockchain:** The target network for all deployments.

### 1.2. Core Components & Terminology

The StacksOrbit project is composed of the following key components:

* **`stacksorbit_cli.py` (formerly `ultimate_stacksorbit.py`):** The primary command-line interface for interacting with the StacksOrbit tool. The "ultimate" terminology was used to signify that this is the main, all-in-one entry point for the tool.
* **`stacksorbit_dashboard.py` (formerly `enhanced_dashboard.py`):** A real-time, interactive dashboard for monitoring the deployment process, network health, and other key metrics. The "enhanced" terminology was used to highlight the advanced, real-time nature of the dashboard.
* **Core Deployer (`enhanced_conxian_deployment.py`):** The main engine for deploying smart contracts. It includes features for smart category recognition, dependency ordering, and parallel deployment.
* **Setup Wizard (`setup_wizard.py`):** An interactive wizard to guide users through the initial setup and configuration of the project.

### 1.2. Features

* **Smart Category Recognition:** Automatically categorizes and deploys smart contracts.
* **Advanced Monitoring Dashboard:** A real-time, interactive dashboard for monitoring deployments.
* **Comprehensive Testing & Verification:** A full suite of tests to ensure the reliability of the tool.
* **User-Friendly Experience:** An interactive setup wizard and clear, concise documentation.

## 2. Installation Guide

### Prerequisites

* Python 3.8+
* Node.js 14+ (for contract testing with Clarinet)
* Git
* Clarinet
* A Stacks account with STX tokens for testnet deployment

### Installation from Source

Currently, StacksOrbit is run directly from the source code.

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/Anya-org/stacksorbit.git
    cd stacksorbit
    ```

2. **Install Dependencies:**

    ```bash
    # Install Python dependencies
    pip install -r requirements.txt

    # Install Node.js dependencies (for Clarinet)
    npm install
    ```

## 3. Getting Started

### 3.1. Configuration

Create a `.env` file in your project root. The easiest way to do this is by running the interactive setup wizard:

```bash
python stacksorbit_cli.py setup
```

The wizard will generate a `.env` file with the following variables:

```env
# Required Variables
DEPLOYER_PRIVKEY=your_private_key_here
SYSTEM_ADDRESS=your_stacks_address_here
NETWORK=testnet

# Local Devnet Configuration
STACKS_CORE_PATH=/path/to/your/stacks-core

# Optional Variables (Recommended)
HIRO_API_KEY=your_hiro_api_key_here
CORE_API_URL=https://api.testnet.hiro.so
STACKS_API_BASE=https://api.testnet.hiro.so

# Deployment Configuration
DEPLOYMENT_MODE=full
BATCH_SIZE=5
PARALLEL_DEPLOY=false

# Monitoring Configuration
MONITORING_ENABLED=true
LOG_LEVEL=INFO
SAVE_LOGS=true
```

### 3.2. Configuration Options

| Variable | Required | Description |
| --- | --- | --- |
| `DEPLOYER_PRIVKEY` | Yes | Your Stacks account private key for deploying contracts. |
| `SYSTEM_ADDRESS` | Yes | Your Stacks address (e.g., `SP...`). |
| `NETWORK` | Yes | The target network for deployment (`devnet`, `testnet`, `mainnet`). |
| `STACKS_CORE_PATH` | No | The local file path to the `stacks-core` repository for running a local devnet. |
| `HIRO_API_KEY` | No | Your Hiro API key for higher rate limits on API requests. |
| `CORE_API_URL` | No | A custom Stacks API endpoint. |
| `DEPLOYMENT_MODE` | No | The deployment mode (`full`, `upgrade`). |
| `BATCH_SIZE` | No | The number of contracts to deploy in a single batch. |
| `PARALLEL_DEPLOY` | No | Whether to enable parallel deployment (`true` or `false`). |
| `MONITORING_ENABLED` | No | Whether to enable real-time monitoring (`true` or `false`). |

## 4. Development

### 3.1. Development Setup

For development, it's recommended to install the Python dependencies in editable mode with the `dev` and `test` extras:

```bash
# Install Python dependencies for development
pip install -e ".[dev,test]"
```

### 3.2. Running Tests

The primary test suite is built with Vitest and the Clarinet SDK. To run the tests, use the following command:

```bash
npm run test:vitest
```

This will execute all of the tests in the `js-tests/` directory.

To check test coverage, you can use the following command:

```bash
npx vitest --coverage
```

### 3.3. Code Style

* **Python:** This project follows the [PEP 8](https://pep8.org/) style guide and uses [Black](https://black.readthedocs.io/) for formatting.

    ```bash
    # Format code
    black stacksorbit.py

    # Lint
    pylint stacksorbit.py

    # Type check
    mypy stacksorbit.py
    ```

* **JavaScript:** This project follows the [StandardJS](https://standardjs.com/) style guide.

    ```bash
    # Lint
    npm run lint
    ```

## 4. Deployment Workflow

The recommended workflow for deploying smart contracts with StacksOrbit is as follows:

1. **Setup and Configuration:**
    Run the interactive setup wizard to configure your deployment environment.

    ```bash
    python stacksorbit_cli.py setup
    ```

2. **Run Pre-Deployment Checks:**
    Before deploying, it's highly recommended to run a comprehensive system diagnosis to ensure everything is configured correctly.

    ```bash
    python stacksorbit_cli.py diagnose --verbose
    ```

3. **Simulate Deployment (Dry Run):**
    Perform a dry run to see which contracts will be deployed and to get a gas estimate. This will not execute any transactions.

    ```bash
    python stacksorbit_cli.py deploy --dry-run
    ```

4. **Deploy to Testnet:**
    Once you've verified the dry run, you can deploy your contracts to the testnet.

    ```bash
    python stacksorbit_cli.py deploy --network testnet
    ```

5. **Monitor the Deployment:**
    Use the monitoring command to track the status of your deployment in real-time.

    ```bash
    python stacksorbit_cli.py monitor --follow
    ```

6. **Verify the Deployment:**
    After the deployment is complete, run the verification command to ensure that all contracts were deployed successfully.

    ```bash
    python stacksorbit_cli.py verify --comprehensive
    ```

## 5. Key Commands

The primary interface for the StacksOrbit tool is the `stacksorbit_cli.py` script. Here are some of the most common commands:

### 5.1. Setup

* **Interactive Setup Wizard:**

    ```bash
    python stacksorbit_cli.py setup
    ```

### 5.2. Deployment

* **Dry Run (Recommended before any deployment):**

    ```bash
    python stacksorbit_cli.py deploy --dry-run
    ```

* **Deploy to Testnet:**

    ```bash
    python stacksorbit_cli.py deploy --network testnet
    ```

* **Deploy a Specific Category:**

    ```bash
    python stacksorbit_cli.py deploy --category core
    ```

### 5.3. Monitoring

* **Launch the Monitoring Dashboard:**

    ```bash
    python stacksorbit_cli.py dashboard
    ```

* **Monitor from the Command Line:**

    ```bash
    python stacksorbit_cli.py monitor --follow
    ```

### 5.4. Verification

* **Comprehensive Verification:**

    ```bash
    python stacksorbit_cli.py verify --comprehensive
    ```

### 5.5. Diagnostics

* **Full System Diagnosis:**

    ```bash
    python stacksorbit_cli.py diagnose --verbose
    ```

### 5.6. Other Commands

* **Auto-Detect Contracts:**

    ```bash
    python stacksorbit_cli.py detect --directory .
    ```

* **Apply a Deployment Template:**

    ```bash
    python stacksorbit_cli.py template --name <template_name>
    ```

* **Manage Local Devnet:**

    ```bash
    python stacksorbit_cli.py devnet --devnet-command <start|stop|status>
    ```

## 6. Troubleshooting Guide

### 6.1. Common Issues

#### Configuration Errors

* **`Missing required configuration`:** This error occurs when one of the required variables (`DEPLOYER_PRIVKEY`, `SYSTEM_ADDRESS`, `NETWORK`) is not set in your `.env` file. Run `python stacksorbit_cli.py setup` to regenerate the file.
* **`Invalid DEPLOYER_PRIVKEY format`:** The private key must be a 64- or 66-character hexadecimal string.
* **`Invalid SYSTEM_ADDRESS format`:** The Stacks address must start with `S` and be between 40 and 42 characters.

#### Deployment Failures

* **`Pre-deployment checks failed`:** Run `python stacksorbit_cli.py diagnose --verbose` to get a detailed report of the issues.
* **`Low balance`:** The account you're using to deploy does not have enough STX to cover the estimated gas fees. You will need to add more STX to your account.
* **`Compilation issues detected`:** This warning indicates that `clarinet check` found issues with your smart contracts. While deployment may still work, it's highly recommended to fix these issues first.

#### Connection Problems

* **`Network check failed`:** This error indicates that the tool could not connect to the Stacks API. Check your internet connection and the status of the Hiro API.
* **`Could not retrieve account information`:** This error can occur if the API is down or if the address in your `.env` file is incorrect.

### 6.2. Log Files

For more detailed error information, you can check the log files, which are saved in the `logs/` directory in your project root.

### 6.3. Getting Help

If you're still having trouble, please open an issue on the [GitHub repository](https://github.com/Anya-org/stacksorbit/issues).

## 7. Contributing

### 7.1. Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/Anya-org/stacksorbit/issues)
2. If not, create a new issue with a clear title, description, and steps to reproduce.

### 7.2. Suggesting Features

1. Check [Discussions](https://github.com/Anya-org/stacksorbit/discussions) for existing suggestions.
2. Create a new discussion with a clear use case and proposed solution.

### 7.3. Pull Requests

1. **Fork** the repository.
2. **Create a branch** from `develop`.
3. **Make your changes** and **test thoroughly**.
4. **Commit** with clear messages (see "Commit Messages" section).
5. **Push** to your fork and **open a Pull Request** to the `develop` branch.

### 7.4. Pull Request Process

1. **Update documentation** if needed.
2. **Add tests** for new features.
3. **Ensure all tests pass**.
4. **Update CHANGELOG.md**.
5. **Request review** from maintainers.

## 8. Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

* `feat`: New feature
* `fix`: Bug fix
* `docs`: Documentation
* `style`: Formatting
* `refactor`: Code restructuring
* `test`: Adding tests
* `chore`: Maintenance

## 9. Release Process

1. Version bump in `package.json` and `setup.py`.
2. Update `CHANGELOG.md`.
3. Create git tag: `v1.x.x`.
4. Push tag: `git push origin v1.x.x`.
5. GitHub Actions handles publishing.

## 8. License

This project is licensed under the MIT License. See the `LICENSE` file for details.
