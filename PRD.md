# StacksOrbit Product Requirements Document (PRD)

## 1. Overview

StacksOrbit is a comprehensive deployment and management tool for the Stacks blockchain. This document outlines the project's migration to a modern, efficient, and synchronized development environment using the Clarinet SDK, Vitest, and Chainhooks. This "Root-Up" methodology ensures that documentation and implementation are always aligned.

## 2. Current Architecture

*   **Contracts:** The project currently contains a single placeholder Clarity contract (`contracts/placeholder.clar`).
*   **Testing:** The existing test suite is a mix of Python and JavaScript-based tests, which will be migrated to Vitest.
*   **Dependencies:** The project relies on a mix of Node.js and Python dependencies.

## 3. Migration Roadmap

The primary goal is to refactor the project to use a modern, streamlined toolchain that leverages the Clarinet SDK for development and testing, and Chainhooks for multi-network event monitoring.

*   **Phase 1: Vitest Integration (Complete)**
    *   [x] Initialize `PRD.md`.
    *   [x] Update `package.json` with `vitest-environment-clarinet`.
    *   [x] Create `vitest.config.mts`.
    *   [x] Migrate existing tests to Vitest.
*   **Phase 2: Chainhook Integration (Complete)**
    *   [x] Create `/chainhooks` directory.
    *   [x] Define Chainhook predicates for contract events.
    *   [x] Implement multi-network monitoring (Devnet, Testnet, Mainnet).
*   **Phase 3: Contract Registry**
    *   [ ] Create a contract registry in this PRD to track deployments across all networks.

## 4. Session Log

### Session 1: Initialization & Alignment

*   **Objective:** Establish the project's foundation by creating the PRD, updating dependencies, and configuring Vitest.
*   **Changes:**
    *   Created `PRD.md`.
    *   Configured Vitest with Clarinet SDK.
    *   Migrated initial placeholder tests.
*   **Status:** Complete.

### Session 2: Chainhook Expansion & Security Hardening

*   **Objective:** Expand Chainhook support for multi-network monitoring and fix configuration validation bugs.
*   **Changes:**
    *   Standardized Vitest config by removing legacy `.js` files and confirming `.mts` for ESM compatibility.
    *   Created network-specific Chainhook predicates (`devnet.json`, `testnet.json`, `mainnet.json`).
    *   Fixed C32 address validation to include '0' and '1', resolving common devnet address failures.
*   **Status:** Complete.

### Session 3: Robustness & Toolchain Cleanup

*   **Objective:** Standardize the toolchain and improve configuration robustness.
*   **Changes:**
    *   Improved `stacksorbit_gui.py` configuration loader to handle quoted values and whitespace correctly.
    *   Verified all system tests pass locally.
*   **Status:** Complete.
