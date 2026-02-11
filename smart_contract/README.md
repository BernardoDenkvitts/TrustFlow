# TrustFlow Escrow Smart Contract

Programmable vault for ETH custody in payment agreements with guarantee. This contract serves as the **financial source of truth** for the TrustFlow, consumed passively by the backend via event polling.

## Overview

The TrustFlowEscrow contract provides:

- **ETH Custody**: Secure storage of funds during agreement lifecycle
- **Arbitration Policies**: Support for `NONE` (payer-only release) and `WITH_ARBITRATOR` (dispute resolution)
- **State Machine**: Deterministic state transitions (CREATED → FUNDED → RELEASED or DISPUTED → RELEASED/REFUNDED)
- **Event Emission**: Complete events for backend synchronization

## Prerequisites

- [Foundry](https://book.getfoundry.sh/getting-started/installation) installed
- Local Ethereum node (Anvil) for development

## Quick Start

### Installation

1. **Initialize Submodules** (after cloning):
   ```bash
   cd TrustFlow/smart_contract
   git submodule update --init --recursive
   ```

2. **Install dependencies**:
   ```bash
   forge install
   ```

### Compile

```bash
forge build
```

### Run Tests

```bash
# Standard test run
forge test
```

### Deploy Locally

1. Start Anvil (local Ethereum node):

```bash
anvil
```

2. Deploy the contract (in another terminal):

```bash
forge script script/Deploy.s.sol --rpc-url http://127.0.0.1:8545 --broadcast
```

## Contract API

### Functions

| Function                                                 | Description                  | Access                                  |
| -------------------------------------------------------- | ---------------------------- | --------------------------------------- |
| `createAgreement(id, payee, arbitrator, amount, policy)` | Creates new escrow agreement | Anyone (becomes payer)                  |
| `fund(id)`                                               | Deposits ETH into agreement  | Payer only                              |
| `openDispute(id)`                                        | Opens dispute (locks funds)  | Payer/Payee (WITH_ARBITRATOR only)      |
| `release(id)`                                            | Releases payment to payee    | Payer (FUNDED) or Arbitrator (DISPUTED) |
| `refund(id)`                                             | Refunds payment to payer     | Arbitrator only (DISPUTED)              |
| `getAgreement(id)`                                       | Returns agreement details    | Anyone (view)                           |
| `getAgreementState(id)`                                  | Returns current state        | Anyone (view)                           |

### Events

```solidity
event AgreementCreated(
    bytes32 indexed agreementId,
    address indexed payer,
    address indexed payee,
    uint256 amount,
    ArbitrationPolicy policy,
    address arbitrator
);

event PaymentFunded(
    bytes32 indexed agreementId,
    address indexed payer,
    uint256 amount
);

event DisputeOpened(
    bytes32 indexed agreementId,
    address indexed openedBy
);

event PaymentReleased(
    bytes32 indexed agreementId,
    address indexed payee,
    uint256 amount
);

event PaymentRefunded(
    bytes32 indexed agreementId,
    address indexed payer,
    uint256 amount
);
```

### Event Signatures for Backend Polling

Use these topic hashes with `eth_getLogs`:

| Event            | Topic0 (keccak256)                         |
| ---------------- | ------------------------------------------ |
| AgreementCreated | `0x...` (use `cast sig-event` to generate) |
| PaymentFunded    | `0x...`                                    |
| DisputeOpened    | `0x...`                                    |
| PaymentReleased  | `0x...`                                    |
| PaymentRefunded  | `0x...`                                    |

Generate with:

```bash
cast sig-event "AgreementCreated(bytes32,address,address,uint256,uint8,address)"
```

## Security Features

- **ReentrancyGuard**: Protection against reentrancy attacks on `release()` and `refund()`
- **Checks-Effects-Interactions**: State updated before ETH transfers
- **Custom Errors**: Gas-efficient error handling with descriptive messages
- **No Admin Functions**: Trustless design with no privileged access

### Test Coverage

The test suite covers:

- ✅ Agreement creation (all policies)
- ✅ Funding validation
- ✅ Dispute mechanics
- ✅ Release flows (payer and arbitrator)
- ✅ Refund flows
- ✅ Permission checks
- ✅ State transition validation
- ✅ Final state immutability
- ✅ Reentrancy protection
- ✅ Fuzz testing for amounts

