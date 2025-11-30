# Conxian ⇄ StacksOrbit ⇄ Conxian_UI Deployment Map

> **Purpose:** This document captures the end‑to‑end mapping between Conxian’s on‑chain modules, the Conxian_UI DApps, and the StacksOrbit deploy / monitor / verify pipeline. It should be read together with:
>
> - Conxian: `Clarinet.toml`, `documentation/architecture/CONXIAN_DAPPS_MAP.md`
> - StacksOrbit: `AGENTS.md`, `enhanced_conxian_deployment.py`, `stacksorbit_cli.py`
> - Conxian_UI: `README.md`, `src/lib/contracts.ts`, `src/app/*`

_Last updated: November 30, 2025_

---

## 1. High‑Level Pipeline

1. **Author & test contracts** in the Conxian repo
   - Source of truth: `Clarinet.toml` + trait files in `contracts/traits/`.
   - Syntax & structure checked via `clarinet check`.

2. **Configure StacksOrbit** in the Conxian project root
   - Run setup wizard from the project root:
     - `stacksorbit setup` (or `python stacksorbit_cli.py setup`).
   - Wizard detects `Clarinet.toml`, writes `.env` with:
     - `DEPLOYER_PRIVKEY`, `SYSTEM_ADDRESS`, `NETWORK`, `BATCH_SIZE`, `PARALLEL_DEPLOY`, etc.

3. **Dry‑run deployments per module / DApp surface**
   - Use StacksOrbit CLI categories (see §2) to preview contract groups:
     - `stacksorbit deploy --dry-run --category dex`
     - `stacksorbit deploy --dry-run --category tokens`
     - `stacksorbit deploy --dry-run --category oracle`
     - etc.

4. **Testnet deployment via StacksOrbit**
   - After dry‑runs and compilation checks:
     - `stacksorbit deploy --category <category>`.
   - Internally calls `EnhancedConxianDeployer.deploy_conxian`, which:
     - Parses `Clarinet.toml`.
     - Filters contracts by category.
     - Sorts them using `_sort_by_dependencies` and deploys in order.

5. **Monitoring & verification**
   - Monitoring (CLI): `stacksorbit monitor --follow`.
   - Dashboard (TUI): `stacksorbit monitor --dashboard` (Textual UI).
   - Verification: `stacksorbit verify --comprehensive`.
   - Diagnostics: `stacksorbit diagnose --verbose`.

6. **Front‑end integration (Conxian_UI)**
   - Conxian_UI reads deployed contract IDs from configuration (`basePrincipal`) and uses:
     - `src/lib/contracts.ts` (`CoreContracts`, `Tokens`).
     - `src/lib/contract-interactions.ts` and Core API ABI lookups.
   - Routes like `/pools`, `/router`, `/tx` rely on the contracts deployed in steps 3–4.

---

## 2. StacksOrbit Categories ↔ Conxian Modules

StacksOrbit’s `EnhancedConxianDeployer` defines loose **categories** (substring filters) over Clarinet contract names. The table below aligns those categories with Conxian’s architecture and DApps.

### 2.1 Category Mapping Table

| StacksOrbit Category | Matching Conxian Modules / Contracts (examples) | DApps / Surfaces | Notes |
|----------------------|--------------------------------------------------|------------------|-------|
| **core** | Traits & utilities: `sip-standards`, `core-protocol`, `defi-primitives`, `dimensional-traits`, `oracle-pricing`, `risk-management`, `math-utilities`, `trait-errors`, `encoding`, `utils`, etc. | All DApps | Must be deployed first; provides shared interfaces and helpers. |
| **tokens** | `cxd-token`, `cxlp-token`, `cxvg-token`, `cxtr-token`, `cxs-token`, `token-system-coordinator`, `cxd-price-initializer` | DEX, Governance, Staking, Vaults | Conxian_UI `Tokens[]` uses `cxd`, `cxvg`, `cxtr`, `cxs`. |
| **governance** | `governance-token`, `proposal-engine`, `proposal-registry`, `governance-voting`, `timelock-controller` | Governance DApp (planned) | Controls param changes and upgrades for DEX, lending, oracles, risk. |
| **dex** | `dex-factory`, `dex-factory-v2`, routers (via remaps, e.g. `multi-hop-router-v3`, `dimensional-advanced-router-dijkstra`), pools (`concentrated-liquidity-pool`, `concentrated-liquidity-pool-v2`, `tiered-pools`, `pool-registry`), vault/pool helpers | DEX (swaps, LP, CLP), `/pools`, `/router`, `/tx` | Primary contracts behind all DEX UI surfaces. |
| **dimensional** | `dim-registry`, `dim-metrics`, `dimensional-core`, `dim-graph`, `dim-oracle-automation`, `dim-yield-stake`, CLP position‑NFT within `concentrated-liquidity-pool` | Core Engine & Dimensional metrics | Drives advanced routing, liquidity graph, and dimensional analytics. |
| **oracle** | `oracle`, `oracle-aggregator-v2`, `dimensional-oracle`, `twap-oracle`, `btc-adapter`, `oracle-adapter` stubs | Price feeds for DEX, Lending, Enterprise | Conxian_UI uses `oracle-aggregator-v2` via `ContractInteractions.getPrice`. |
| **security** | `circuit-breaker`, `mev-protector`, `mev-protector-root`, `ownable`, `pausable`, roles & RBAC | Circuit breakers, MEV protection, access controls | Used by DEX, lending, governance. Critical for safe deployment. |
| **monitoring** | `analytics-aggregator`, `finance-metrics`, `protocol-invariant-monitor`, any `monitoring-dashboard` contracts | Monitoring dashboards, analytics | Feeds both on‑chain analytics and StacksOrbit/enterprise dashboards. |
| **self-run** / **self-managed** | Placeholder patterns (`self-run`, `autonomous`, etc.) | N/A (future) | No matching contracts yet; filters currently no‑op. |

**Important:** Category membership is purely name‑based (substring matching). The authoritative list of contracts and their roles remains `Clarinet.toml` and `CONXIAN_DAPPS_MAP.md`.

---

## 3. DApps → Categories → CLI Commands

### 3.1 DEX DApp (Swaps, LP, Router, Pools)

- **Key contracts** (Conxian view):
  - Factory & pools: `dex-factory`, `dex-factory-v2`, `concentrated-liquidity-pool`, `concentrated-liquidity-pool-v2`, `tiered-pools`, `pool-registry`.
  - Routers: `multi-hop-router-v3`, `dimensional-advanced-router-dijkstra`.
  - Helpers: `oracle`, `oracle-aggregator-v2`, `manipulation-detector`, `rebalancing-rules`, `batch-auction`.
- **Conxian_UI dependencies**:
  - `CoreContracts` (now aligned):
    - `concentrated-liquidity-pool` (primary pool), `dex-factory-v2`, `dex-router` (via remap), `multi-hop-router-v3`, `bond-factory`.
  - Routes:
    - `/pools` – pool KPIs (reserves, TVL, fees, performance).
    - `/router` – multi‑hop path estimation using on‑chain router.
    - `/tx` – generic contract call builder with DEX templates.
- **Recommended StacksOrbit categories** for DEX deployments:
  - `core`, `tokens`, `dex`, `dimensional`, `oracle`, `security`, `monitoring`.
- **Example CLI sequence (testnet):**
  - Dry run:
    - `stacksorbit deploy --dry-run --category core`
    - `stacksorbit deploy --dry-run --category tokens`
    - `stacksorbit deploy --dry-run --category oracle`
    - `stacksorbit deploy --dry-run --category dimensional`
    - `stacksorbit deploy --dry-run --category dex`
  - Deploy:
    - `stacksorbit deploy --category core`
    - `stacksorbit deploy --category tokens`
    - `stacksorbit deploy --category oracle`
    - `stacksorbit deploy --category dimensional`
    - `stacksorbit deploy --category dex`
  - Monitor / verify:
    - `stacksorbit monitor --follow`
    - `stacksorbit verify --comprehensive`

### 3.2 Tokens & Vaults

- **Contracts**:
  - Tokens: `cxd-token`, `cxlp-token`, `cxvg-token`, `cxtr-token`, `cxs-token`, `token-system-coordinator`, `cxd-price-initializer`.
  - Vaults & sBTC integration: `sbtc-vault`, `sbtc-integration`, `btc-adapter`, `dlc-manager`.
- **Conxian_UI**:
  - `Tokens[]` for token selection and SIP‑010 templates in `/tx`.
  - Vault balances via `getVaultBalance()` using `CoreContracts` vault entries.
- **StacksOrbit categories**:
  - `core`, `tokens`, `oracle` (for pricing), `security`, `monitoring`.

### 3.3 Governance

- **Contracts**:
  - `governance-token`, `proposal-engine`, `proposal-registry`, `governance-voting`, `timelock-controller`.
- **DApp**:
  - Governance UI (planned): create proposals, vote, execute with timelock.
- **StacksOrbit**:
  - Deploy with `core`, `tokens`, `governance`, `security`, `monitoring`.
  - Use `stacksorbit verify` to confirm governance wiring before enabling parameter changes for other modules.

### 3.4 Lending & Enterprise

- **Contracts** (Conxian DApps map):
  - Lending engine: `comprehensive-lending-system`, `liquidation-manager`, `interest-rate-model`.
  - Risk: `risk-manager`, `liquidation-engine`, `funding-calculator`.
  - Enterprise: `enterprise-api`, `enterprise-loan-manager`.
- **Current UI**:
  - Primarily CLI/tests driven (no dedicated Conxian_UI screens yet).
- **StacksOrbit categories**:
  - No explicit `lending` / `enterprise` categories; contracts fall under `core`, `dimensional`, `oracle`, `security`, and `other`.
  - Deployment is handled via **full manifest** or by selective contract lists in the setup wizard.

### 3.5 Monitoring & Analytics

- **Contracts**:
  - `analytics-aggregator`, `finance-metrics`, `protocol-invariant-monitor`, plus any `monitoring-dashboard` contracts.
- **DApps**:
  - On‑chain monitoring surfaces; off‑chain dashboards (StacksOrbit TUI and potential web dashboards) read from these.
- **StacksOrbit**:
  - Category: `monitoring`.
  - CLI:
    - `stacksorbit monitor --dashboard` – live view of API status, block height, accounts, and (optionally) deployment state.

---

## 4. Compliance & Risk Hooks

Conxian and StacksOrbit are designed to accommodate regulatory and risk oversight (e.g., FSCA/IFWG/Markaicode‑style expectations) without hard‑coding specific jurisdictional rules.

### 4.1 On‑Chain Compliance Anchors (Conxian)

- **Audit & attestations**:
  - `audit-registry`, `audit-badge-nft` – register audits, store attestations, issue badges.
- **Security / invariants**:
  - `circuit-breaker`, `mev-protector`, `protocol-invariant-monitor` – provide explicit hooks for pausing, MEV detection, and invariant checks.
- **Enterprise APIs**:
  - `enterprise-api`, `enterprise-loan-manager` – structured entry points for institutional flows, with room for KYB/KYC attestations at the API level.

### 4.2 StacksOrbit Touchpoints

- **Pre‑deployment checks** (`run_pre_checks` in `EnhancedConxianDeployer`):
  - Can be extended to require:
    - Presence of `audit-registry` and `protocol-invariant-monitor` in the expected deployment set.
    - Successful `clarinet check` + test suite pass before allowing mainnet deployment.
- **Verification stage** (`DeploymentVerifier`, `stacksorbit verify`):
  - Can include:
    - Queries to `audit-registry` to ensure required audits are registered.
    - Read‑only calls to `protocol-invariant-monitor` and `finance-metrics` to confirm invariants pre/post‑deployment.
- **Monitoring / chainhooks**:
  - Chainhook processes (e.g., `chainhooks_manager.py`) can subscribe to:
    - DEX swaps and LP events.
    - Lending liquidations.
    - Governance proposal / execution events.
  - These can then feed into enterprise/compliance tools for:
    - Transaction pattern analysis.
    - Risk threshold alerts.
    - Audit trail generation.

### 4.3 Suggested Compliance Flow

1. **Pre‑deployment gate** (testnet & mainnet):
   - `clarinet check` clean + key tests passing.
   - StacksOrbit `diagnose` and `verify` confirm:
     - Core, DEX, oracle, security, monitoring modules present.
     - `audit-registry` & `protocol-invariant-monitor` deployed.

2. **Deployment** (via categories):
   - Deploy `core` → `tokens` → `oracle` → `dimensional` → `dex` → `governance` → `monitoring`.

3. **Post‑deployment verification**:
   - `stacksorbit verify --comprehensive` + custom checks against:
     - `audit-registry` (expected audits).
     - `protocol-invariant-monitor` (core invariants OK).
     - `finance-metrics` (sanity metrics for TVL, utilization, spreads).

4. **Ongoing monitoring**:
   - StacksOrbit `monitor --follow` or dashboard for technical health.
   - Chainhooks / external services consuming events from:
     - DEX (swaps, LP changes, price feeds).
     - Lending & risk (liquidations, funding rates).
     - Governance (proposals, votes, executions).

---

## 5. How to Use This Map

- **Protocol / backend engineers**
  - Use this to plan per‑category deployments and to verify that all modules required by a given DApp surface are present before UI integration.
- **Frontend / UX teams (Conxian_UI)**
  - When adding a route or template, ensure the backing contracts are:
    - Listed in `Clarinet.toml` and `CONXIAN_DAPPS_MAP.md`.
    - Covered by at least one StacksOrbit category.
    - Exposed via `CoreContracts` / `Tokens` with the correct IDs.
- **DevOps / SRE / compliance**
  - Treat this mapping as the **deployment playbook** for Conxian.
  - Extend StacksOrbit pre‑checks, verification, and monitoring to call the right Conxian contracts (e.g. `audit-registry`, `protocol-invariant-monitor`, `finance-metrics`) as part of your operational runbooks.

This document is meant to stay in sync with:

- Conxian’s `Clarinet.toml` and `CONXIAN_DAPPS_MAP.md`.
- StacksOrbit’s `AGENTS.md`, `enhanced_conxian_deployment.py`, and `stacksorbit_cli.py`.
- Conxian_UI’s `README.md` and `src/lib/contracts.ts`.

When any of those change materially, update this map accordingly.
