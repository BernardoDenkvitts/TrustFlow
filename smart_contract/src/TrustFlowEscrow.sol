// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title TrustFlowEscrow
 * @notice Programmable vault for ETH custody in payment agreements with guarantee.
 * @dev Acts as the financial source of truth, consumed passively by the backend via event polling.
 *      The contract does NOT manage users, authentication, or complex business logic.
 *      It only validates critical financial rules and emits complete events.
 */
contract TrustFlowEscrow is ReentrancyGuard {
    // ============ Enums ============

    /// @notice Arbitration policy for the agreement
    enum ArbitrationPolicy {
        NONE,           // No arbitrator, only payer can release
        WITH_ARBITRATOR // Arbitrator can resolve disputes
    }

    /// @notice Financial state of the agreement
    enum AgreementState {
        CREATED,    // Agreement created, awaiting funding
        FUNDED,     // ETH deposited, awaiting release or dispute
        DISPUTED,   // Dispute opened, only arbitrator can decide
        RELEASED,   // Payment released to payee (final state)
        REFUNDED    // Payment refunded to payer (final state)
    }

    // ============ Structs ============

    /// @notice Agreement data structure
    struct Agreement {
        bytes32 agreementId;        // Unique ID (provided by backend)
        address payer;              // Depositor
        address payee;              // Receiver
        address arbitrator;         // Mediator (address(0) if NONE policy)
        uint256 amount;             // Value in wei
        ArbitrationPolicy policy;   // NONE or WITH_ARBITRATOR
        AgreementState state;       // Current financial state
    }

    // ============ Storage ============

    /// @notice Mapping of agreementId to Agreement
    mapping(bytes32 => Agreement) public agreements;

    // ============ Events ============

    /// @notice Emitted when a new agreement is created
    event AgreementCreated(
        bytes32 indexed agreementId,
        address indexed payer,
        address indexed payee,
        uint256 amount,
        ArbitrationPolicy policy,
        address arbitrator
    );

    /// @notice Emitted when an agreement is funded
    event PaymentFunded(
        bytes32 indexed agreementId,
        address indexed payer,
        uint256 amount
    );

    /// @notice Emitted when a dispute is opened
    event DisputeOpened(
        bytes32 indexed agreementId,
        address indexed openedBy
    );

    /// @notice Emitted when payment is released to payee
    event PaymentReleased(
        bytes32 indexed agreementId,
        address indexed payee,
        uint256 amount
    );

    /// @notice Emitted when payment is refunded to payer
    event PaymentRefunded(
        bytes32 indexed agreementId,
        address indexed payer,
        uint256 amount
    );

    // ============ Errors ============

    error AgreementAlreadyExists(bytes32 agreementId);
    error AgreementNotFound(bytes32 agreementId);
    error InvalidPayee();
    error InvalidAmount();
    error InvalidArbitratorForPolicy();
    error ArbitratorCannotBePayer();
    error ArbitratorCannotBePayee();
    error OnlyPayer();
    error OnlyPayerOrPayee();
    error OnlyArbitrator();
    error InvalidState(AgreementState current, AgreementState expected);
    error InvalidStateForAction(AgreementState current);
    error IncorrectPaymentValue(uint256 sent, uint256 expected);
    error DisputeNotAllowed();
    error TransferFailed();
    error Unauthorized();

    // ============ Modifiers ============

    /// @notice Ensures agreement exists
    modifier agreementExists(bytes32 agreementId) {
        if (agreements[agreementId].payer == address(0)) {
            revert AgreementNotFound(agreementId);
        }
        _;
    }

    // ============ External Functions ============

    /**
     * @notice Creates a new escrow agreement
     * @param agreementId Unique identifier provided by the backend
     * @param payee Address that will receive the payment
     * @param arbitrator Address of the arbitrator (address(0) if NONE policy)
     * @param amount Amount in wei to be escrowed
     * @param policy Arbitration policy (NONE or WITH_ARBITRATOR)
     */
    function createAgreement(
        bytes32 agreementId,
        address payee,
        address arbitrator,
        uint256 amount,
        ArbitrationPolicy policy
    ) external {
        // Validate agreementId doesn't exist
        if (agreements[agreementId].payer != address(0)) {
            revert AgreementAlreadyExists(agreementId);
        }

        // Validate payee
        if (payee == address(0)) {
            revert InvalidPayee();
        }

        // Validate amount
        if (amount == 0) {
            revert InvalidAmount();
        }

        // Validate arbitrator based on policy
        if (policy == ArbitrationPolicy.NONE) {
            if (arbitrator != address(0)) {
                revert InvalidArbitratorForPolicy();
            }
        } else {
            // WITH_ARBITRATOR
            if (arbitrator == address(0)) {
                revert InvalidArbitratorForPolicy();
            }
            if (arbitrator == msg.sender) {
                revert ArbitratorCannotBePayer();
            }
            if (arbitrator == payee) {
                revert ArbitratorCannotBePayee();
            }
        }

        // Create agreement
        agreements[agreementId] = Agreement({
            agreementId: agreementId,
            payer: msg.sender,
            payee: payee,
            arbitrator: arbitrator,
            amount: amount,
            policy: policy,
            state: AgreementState.CREATED
        });

        emit AgreementCreated(
            agreementId,
            msg.sender,
            payee,
            amount,
            policy,
            arbitrator
        );
    }

    /**
     * @notice Funds an existing agreement with ETH
     * @param agreementId The agreement to fund
     */
    function fund(bytes32 agreementId) external payable agreementExists(agreementId) {
        Agreement storage agreement = agreements[agreementId];

        // Only payer can fund
        if (msg.sender != agreement.payer) {
            revert OnlyPayer();
        }

        // Must be in CREATED state
        if (agreement.state != AgreementState.CREATED) {
            revert InvalidState(agreement.state, AgreementState.CREATED);
        }

        // Must send exact amount
        if (msg.value != agreement.amount) {
            revert IncorrectPaymentValue(msg.value, agreement.amount);
        }

        // Update state (Checks-Effects-Interactions: update state before any external calls)
        agreement.state = AgreementState.FUNDED;

        emit PaymentFunded(agreementId, msg.sender, msg.value);
    }

    /**
     * @notice Opens a dispute for an agreement (only WITH_ARBITRATOR policy)
     * @param agreementId The agreement to dispute
     */
    function openDispute(bytes32 agreementId) external agreementExists(agreementId) {
        Agreement storage agreement = agreements[agreementId];

        // Only WITH_ARBITRATOR policy allows disputes
        if (agreement.policy != ArbitrationPolicy.WITH_ARBITRATOR) {
            revert DisputeNotAllowed();
        }

        // Must be in FUNDED state
        if (agreement.state != AgreementState.FUNDED) {
            revert InvalidState(agreement.state, AgreementState.FUNDED);
        }

        // Only payer or payee can open dispute
        if (msg.sender != agreement.payer && msg.sender != agreement.payee) {
            revert OnlyPayerOrPayee();
        }

        // Update state
        agreement.state = AgreementState.DISPUTED;

        emit DisputeOpened(agreementId, msg.sender);
    }

    /**
     * @notice Releases the payment to the payee
     * @dev Access control:
     *      - NONE policy: only payer (from FUNDED state)
     *      - WITH_ARBITRATOR + FUNDED: only payer
     *      - WITH_ARBITRATOR + DISPUTED: only arbitrator
     * @param agreementId The agreement to release
     */
    function release(bytes32 agreementId) external nonReentrant agreementExists(agreementId) {
        Agreement storage agreement = agreements[agreementId];

        // Validate state
        if (agreement.state != AgreementState.FUNDED && agreement.state != AgreementState.DISPUTED) {
            revert InvalidStateForAction(agreement.state);
        }

        // Check permissions based on policy and state
        if (agreement.policy == ArbitrationPolicy.NONE) {
            // NONE policy: only payer can release
            if (msg.sender != agreement.payer) {
                revert OnlyPayer();
            }
        } else {
            // WITH_ARBITRATOR policy
            if (agreement.state == AgreementState.FUNDED) {
                // In FUNDED state: only payer can release
                if (msg.sender != agreement.payer) {
                    revert OnlyPayer();
                }
            } else {
                // In DISPUTED state: only arbitrator can release
                if (msg.sender != agreement.arbitrator) {
                    revert OnlyArbitrator();
                }
            }
        }

        // Cache values before state change
        uint256 amount = agreement.amount;
        address payee = agreement.payee;

        // Update state BEFORE transfer (Checks-Effects-Interactions pattern)
        agreement.state = AgreementState.RELEASED;

        // Transfer ETH to payee
        (bool success, ) = payee.call{value: amount}("");
        if (!success) {
            revert TransferFailed();
        }

        emit PaymentReleased(agreementId, payee, amount);
    }

    /**
     * @notice Refunds the payment to the payer
     * @dev Only arbitrator can refund, and only from DISPUTED state
     * @param agreementId The agreement to refund
     */
    function refund(bytes32 agreementId) external nonReentrant agreementExists(agreementId) {
        Agreement storage agreement = agreements[agreementId];

        // Must be in DISPUTED state
        if (agreement.state != AgreementState.DISPUTED) {
            revert InvalidState(agreement.state, AgreementState.DISPUTED);
        }

        // Only arbitrator can refund
        if (msg.sender != agreement.arbitrator) {
            revert OnlyArbitrator();
        }

        // Cache values before state change
        uint256 amount = agreement.amount;
        address payer = agreement.payer;

        // Update state BEFORE transfer (Checks-Effects-Interactions pattern)
        agreement.state = AgreementState.REFUNDED;

        // Transfer ETH back to payer
        (bool success, ) = payer.call{value: amount}("");
        if (!success) {
            revert TransferFailed();
        }

        emit PaymentRefunded(agreementId, payer, amount);
    }

    // ============ View Functions ============

    /**
     * @notice Returns the full agreement data
     * @param agreementId The agreement to query
     * @return The Agreement struct
     */
    function getAgreement(bytes32 agreementId) external view returns (Agreement memory) {
        return agreements[agreementId];
    }

    /**
     * @notice Returns the current state of an agreement
     * @param agreementId The agreement to query
     * @return The current AgreementState
     */
    function getAgreementState(bytes32 agreementId) external view returns (AgreementState) {
        return agreements[agreementId].state;
    }
}
