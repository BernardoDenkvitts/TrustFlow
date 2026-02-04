// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test, console} from "forge-std/Test.sol";
import {TrustFlowEscrow} from "../src/TrustFlowEscrow.sol";

/**
 * @title TrustFlowEscrowTest
 * @notice Comprehensive test suite for TrustFlowEscrow contract
 */
contract TrustFlowEscrowTest is Test {
    TrustFlowEscrow public escrow;

    // Test addresses
    address public payer = makeAddr("payer");
    address public payee = makeAddr("payee");
    address public arbitrator = makeAddr("arbitrator");
    address public outsider = makeAddr("outsider");

    // Test values
    bytes32 public agreementId = keccak256("agreement-1");
    uint256 public constant AMOUNT = 1 ether;

    // Events to test
    event AgreementCreated(
        bytes32 indexed agreementId,
        address indexed payer,
        address indexed payee,
        uint256 amount,
        TrustFlowEscrow.ArbitrationPolicy policy,
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

    function setUp() public {
        escrow = new TrustFlowEscrow();
        vm.deal(payer, 10 ether);
        vm.deal(payee, 1 ether);
        vm.deal(outsider, 10 ether);
    }

    // ============ Helper Functions ============

    function _createAgreementNone() internal {
        vm.prank(payer);
        escrow.createAgreement(
            agreementId,
            payee,
            address(0),
            AMOUNT,
            TrustFlowEscrow.ArbitrationPolicy.NONE
        );
    }

    function _createAgreementWithArbitrator() internal {
        vm.prank(payer);
        escrow.createAgreement(
            agreementId,
            payee,
            arbitrator,
            AMOUNT,
            TrustFlowEscrow.ArbitrationPolicy.WITH_ARBITRATOR
        );
    }

    function _fundAgreement() internal {
        vm.prank(payer);
        escrow.fund{value: AMOUNT}(agreementId);
    }

    // ============ Creation Tests ============

    function test_CreateAgreement_None_Success() public {
        vm.expectEmit(true, true, true, true);
        emit AgreementCreated(
            agreementId,
            payer,
            payee,
            AMOUNT,
            TrustFlowEscrow.ArbitrationPolicy.NONE,
            address(0)
        );

        _createAgreementNone();

        TrustFlowEscrow.Agreement memory agreement = escrow.getAgreement(agreementId);
        assertEq(agreement.payer, payer);
        assertEq(agreement.payee, payee);
        assertEq(agreement.arbitrator, address(0));
        assertEq(agreement.amount, AMOUNT);
        assertEq(uint8(agreement.policy), uint8(TrustFlowEscrow.ArbitrationPolicy.NONE));
        assertEq(uint8(agreement.state), uint8(TrustFlowEscrow.AgreementState.CREATED));
    }

    function test_CreateAgreement_WithArbitrator_Success() public {
        vm.expectEmit(true, true, true, true);
        emit AgreementCreated(
            agreementId,
            payer,
            payee,
            AMOUNT,
            TrustFlowEscrow.ArbitrationPolicy.WITH_ARBITRATOR,
            arbitrator
        );

        _createAgreementWithArbitrator();

        TrustFlowEscrow.Agreement memory agreement = escrow.getAgreement(agreementId);
        assertEq(agreement.payer, payer);
        assertEq(agreement.payee, payee);
        assertEq(agreement.arbitrator, arbitrator);
        assertEq(agreement.amount, AMOUNT);
        assertEq(uint8(agreement.policy), uint8(TrustFlowEscrow.ArbitrationPolicy.WITH_ARBITRATOR));
        assertEq(uint8(agreement.state), uint8(TrustFlowEscrow.AgreementState.CREATED));
    }

    function test_CreateAgreement_RevertIf_DuplicateId() public {
        _createAgreementNone();

        vm.expectRevert(abi.encodeWithSelector(TrustFlowEscrow.AgreementAlreadyExists.selector, agreementId));
        vm.prank(payer);
        escrow.createAgreement(
            agreementId,
            payee,
            address(0),
            AMOUNT,
            TrustFlowEscrow.ArbitrationPolicy.NONE
        );
    }

    function test_CreateAgreement_RevertIf_InvalidPayee() public {
        vm.expectRevert(TrustFlowEscrow.InvalidPayee.selector);
        vm.prank(payer);
        escrow.createAgreement(
            agreementId,
            address(0),
            address(0),
            AMOUNT,
            TrustFlowEscrow.ArbitrationPolicy.NONE
        );
    }

    function test_CreateAgreement_RevertIf_ZeroAmount() public {
        vm.expectRevert(TrustFlowEscrow.InvalidAmount.selector);
        vm.prank(payer);
        escrow.createAgreement(
            agreementId,
            payee,
            address(0),
            0,
            TrustFlowEscrow.ArbitrationPolicy.NONE
        );
    }

    function test_CreateAgreement_RevertIf_NoneWithArbitrator() public {
        vm.expectRevert(TrustFlowEscrow.InvalidArbitratorForPolicy.selector);
        vm.prank(payer);
        escrow.createAgreement(
            agreementId,
            payee,
            arbitrator,
            AMOUNT,
            TrustFlowEscrow.ArbitrationPolicy.NONE
        );
    }

    function test_CreateAgreement_RevertIf_WithArbitratorNoArbitrator() public {
        vm.expectRevert(TrustFlowEscrow.InvalidArbitratorForPolicy.selector);
        vm.prank(payer);
        escrow.createAgreement(
            agreementId,
            payee,
            address(0),
            AMOUNT,
            TrustFlowEscrow.ArbitrationPolicy.WITH_ARBITRATOR
        );
    }

    function test_CreateAgreement_RevertIf_ArbitratorIsPayer() public {
        vm.expectRevert(TrustFlowEscrow.ArbitratorCannotBePayer.selector);
        vm.prank(payer);
        escrow.createAgreement(
            agreementId,
            payee,
            payer,
            AMOUNT,
            TrustFlowEscrow.ArbitrationPolicy.WITH_ARBITRATOR
        );
    }

    function test_CreateAgreement_RevertIf_ArbitratorIsPayee() public {
        vm.expectRevert(TrustFlowEscrow.ArbitratorCannotBePayee.selector);
        vm.prank(payer);
        escrow.createAgreement(
            agreementId,
            payee,
            payee,
            AMOUNT,
            TrustFlowEscrow.ArbitrationPolicy.WITH_ARBITRATOR
        );
    }

    // ============ Funding Tests ============

    function test_Fund_Success() public {
        _createAgreementNone();

        uint256 contractBalanceBefore = address(escrow).balance;

        vm.expectEmit(true, true, true, true);
        emit PaymentFunded(agreementId, payer, AMOUNT);

        _fundAgreement();

        assertEq(address(escrow).balance, contractBalanceBefore + AMOUNT);
        assertEq(uint8(escrow.getAgreementState(agreementId)), uint8(TrustFlowEscrow.AgreementState.FUNDED));
    }

    function test_Fund_RevertIf_NotPayer() public {
        _createAgreementNone();

        vm.expectRevert(TrustFlowEscrow.OnlyPayer.selector);
        vm.prank(outsider);
        escrow.fund{value: AMOUNT}(agreementId);
    }

    function test_Fund_RevertIf_IncorrectAmount() public {
        _createAgreementNone();

        vm.expectRevert(abi.encodeWithSelector(TrustFlowEscrow.IncorrectPaymentValue.selector, 0.5 ether, AMOUNT));
        vm.prank(payer);
        escrow.fund{value: 0.5 ether}(agreementId);
    }

    function test_Fund_RevertIf_AlreadyFunded() public {
        _createAgreementNone();
        _fundAgreement();

        vm.expectRevert(abi.encodeWithSelector(
            TrustFlowEscrow.InvalidState.selector,
            TrustFlowEscrow.AgreementState.FUNDED,
            TrustFlowEscrow.AgreementState.CREATED
        ));
        vm.prank(payer);
        escrow.fund{value: AMOUNT}(agreementId);
    }

    function test_Fund_RevertIf_AgreementNotFound() public {
        bytes32 nonExistentId = keccak256("non-existent");
        vm.expectRevert(abi.encodeWithSelector(TrustFlowEscrow.AgreementNotFound.selector, nonExistentId));
        vm.prank(payer);
        escrow.fund{value: AMOUNT}(nonExistentId);
    }

    // ============ Dispute Tests ============

    function test_OpenDispute_ByPayer_Success() public {
        _createAgreementWithArbitrator();
        _fundAgreement();

        vm.expectEmit(true, true, true, true);
        emit DisputeOpened(agreementId, payer);

        vm.prank(payer);
        escrow.openDispute(agreementId);

        assertEq(uint8(escrow.getAgreementState(agreementId)), uint8(TrustFlowEscrow.AgreementState.DISPUTED));
    }

    function test_OpenDispute_ByPayee_Success() public {
        _createAgreementWithArbitrator();
        _fundAgreement();

        vm.expectEmit(true, true, true, true);
        emit DisputeOpened(agreementId, payee);

        vm.prank(payee);
        escrow.openDispute(agreementId);

        assertEq(uint8(escrow.getAgreementState(agreementId)), uint8(TrustFlowEscrow.AgreementState.DISPUTED));
    }

    function test_OpenDispute_RevertIf_PolicyNone() public {
        _createAgreementNone();
        _fundAgreement();

        vm.expectRevert(TrustFlowEscrow.DisputeNotAllowed.selector);
        vm.prank(payer);
        escrow.openDispute(agreementId);
    }

    function test_OpenDispute_RevertIf_NotFunded() public {
        _createAgreementWithArbitrator();

        vm.expectRevert(abi.encodeWithSelector(
            TrustFlowEscrow.InvalidState.selector,
            TrustFlowEscrow.AgreementState.CREATED,
            TrustFlowEscrow.AgreementState.FUNDED
        ));
        vm.prank(payer);
        escrow.openDispute(agreementId);
    }

    function test_OpenDispute_RevertIf_Outsider() public {
        _createAgreementWithArbitrator();
        _fundAgreement();

        vm.expectRevert(TrustFlowEscrow.OnlyPayerOrPayee.selector);
        vm.prank(outsider);
        escrow.openDispute(agreementId);
    }

    // ============ Release Tests ============

    function test_Release_ByPayer_NonePolicy_Success() public {
        _createAgreementNone();
        _fundAgreement();

        uint256 payeeBalanceBefore = payee.balance;

        vm.expectEmit(true, true, true, true);
        emit PaymentReleased(agreementId, payee, AMOUNT);

        vm.prank(payer);
        escrow.release(agreementId);

        assertEq(payee.balance, payeeBalanceBefore + AMOUNT);
        assertEq(uint8(escrow.getAgreementState(agreementId)), uint8(TrustFlowEscrow.AgreementState.RELEASED));
    }

    function test_Release_ByPayer_WithArbitrator_Funded_Success() public {
        _createAgreementWithArbitrator();
        _fundAgreement();

        uint256 payeeBalanceBefore = payee.balance;

        vm.prank(payer);
        escrow.release(agreementId);

        assertEq(payee.balance, payeeBalanceBefore + AMOUNT);
        assertEq(uint8(escrow.getAgreementState(agreementId)), uint8(TrustFlowEscrow.AgreementState.RELEASED));
    }

    function test_Release_ByArbitrator_Disputed_Success() public {
        _createAgreementWithArbitrator();
        _fundAgreement();

        vm.prank(payer);
        escrow.openDispute(agreementId);

        uint256 payeeBalanceBefore = payee.balance;

        vm.expectEmit(true, true, true, true);
        emit PaymentReleased(agreementId, payee, AMOUNT);

        vm.prank(arbitrator);
        escrow.release(agreementId);

        assertEq(payee.balance, payeeBalanceBefore + AMOUNT);
        assertEq(uint8(escrow.getAgreementState(agreementId)), uint8(TrustFlowEscrow.AgreementState.RELEASED));
    }

    function test_Release_RevertIf_NotPayer_NonePolicy() public {
        _createAgreementNone();
        _fundAgreement();

        vm.expectRevert(TrustFlowEscrow.OnlyPayer.selector);
        vm.prank(outsider);
        escrow.release(agreementId);
    }

    function test_Release_RevertIf_NotPayer_WithArbitrator_Funded() public {
        _createAgreementWithArbitrator();
        _fundAgreement();

        vm.expectRevert(TrustFlowEscrow.OnlyPayer.selector);
        vm.prank(arbitrator);
        escrow.release(agreementId);
    }

    function test_Release_RevertIf_NotArbitrator_Disputed() public {
        _createAgreementWithArbitrator();
        _fundAgreement();

        vm.prank(payer);
        escrow.openDispute(agreementId);

        vm.expectRevert(TrustFlowEscrow.OnlyArbitrator.selector);
        vm.prank(payer);
        escrow.release(agreementId);
    }

    function test_Release_RevertIf_WrongState() public {
        _createAgreementNone();

        vm.expectRevert(abi.encodeWithSelector(
            TrustFlowEscrow.InvalidStateForAction.selector,
            TrustFlowEscrow.AgreementState.CREATED
        ));
        vm.prank(payer);
        escrow.release(agreementId);
    }

    function test_Release_RevertIf_AlreadyReleased() public {
        _createAgreementNone();
        _fundAgreement();

        vm.prank(payer);
        escrow.release(agreementId);

        vm.expectRevert(abi.encodeWithSelector(
            TrustFlowEscrow.InvalidStateForAction.selector,
            TrustFlowEscrow.AgreementState.RELEASED
        ));
        vm.prank(payer);
        escrow.release(agreementId);
    }

    // ============ Refund Tests ============

    function test_Refund_ByArbitrator_Success() public {
        _createAgreementWithArbitrator();
        _fundAgreement();

        vm.prank(payer);
        escrow.openDispute(agreementId);

        uint256 payerBalanceBefore = payer.balance;

        vm.expectEmit(true, true, true, true);
        emit PaymentRefunded(agreementId, payer, AMOUNT);

        vm.prank(arbitrator);
        escrow.refund(agreementId);

        assertEq(payer.balance, payerBalanceBefore + AMOUNT);
        assertEq(uint8(escrow.getAgreementState(agreementId)), uint8(TrustFlowEscrow.AgreementState.REFUNDED));
    }

    function test_Refund_RevertIf_NotDisputed() public {
        _createAgreementWithArbitrator();
        _fundAgreement();

        vm.expectRevert(abi.encodeWithSelector(
            TrustFlowEscrow.InvalidState.selector,
            TrustFlowEscrow.AgreementState.FUNDED,
            TrustFlowEscrow.AgreementState.DISPUTED
        ));
        vm.prank(arbitrator);
        escrow.refund(agreementId);
    }

    function test_Refund_RevertIf_NotArbitrator() public {
        _createAgreementWithArbitrator();
        _fundAgreement();

        vm.prank(payer);
        escrow.openDispute(agreementId);

        vm.expectRevert(TrustFlowEscrow.OnlyArbitrator.selector);
        vm.prank(payer);
        escrow.refund(agreementId);
    }

    function test_Refund_RevertIf_AlreadyRefunded() public {
        _createAgreementWithArbitrator();
        _fundAgreement();

        vm.prank(payer);
        escrow.openDispute(agreementId);

        vm.prank(arbitrator);
        escrow.refund(agreementId);

        vm.expectRevert(abi.encodeWithSelector(
            TrustFlowEscrow.InvalidState.selector,
            TrustFlowEscrow.AgreementState.REFUNDED,
            TrustFlowEscrow.AgreementState.DISPUTED
        ));
        vm.prank(arbitrator);
        escrow.refund(agreementId);
    }

    // ============ State Immutability Tests ============

    function test_FinalState_Released_CannotTransition() public {
        _createAgreementWithArbitrator();
        _fundAgreement();

        vm.prank(payer);
        escrow.release(agreementId);

        // Cannot fund again
        vm.expectRevert(abi.encodeWithSelector(
            TrustFlowEscrow.InvalidState.selector,
            TrustFlowEscrow.AgreementState.RELEASED,
            TrustFlowEscrow.AgreementState.CREATED
        ));
        vm.prank(payer);
        escrow.fund{value: AMOUNT}(agreementId);

        // Cannot dispute
        vm.expectRevert(abi.encodeWithSelector(
            TrustFlowEscrow.InvalidState.selector,
            TrustFlowEscrow.AgreementState.RELEASED,
            TrustFlowEscrow.AgreementState.FUNDED
        ));
        vm.prank(payer);
        escrow.openDispute(agreementId);
    }

    function test_FinalState_Refunded_CannotTransition() public {
        _createAgreementWithArbitrator();
        _fundAgreement();

        vm.prank(payer);
        escrow.openDispute(agreementId);

        vm.prank(arbitrator);
        escrow.refund(agreementId);

        // Cannot release
        vm.expectRevert(abi.encodeWithSelector(
            TrustFlowEscrow.InvalidStateForAction.selector,
            TrustFlowEscrow.AgreementState.REFUNDED
        ));
        vm.prank(arbitrator);
        escrow.release(agreementId);
    }

    // ============ Reentrancy Tests ============

    function test_Release_Protected_Against_Reentrancy() public {
        // Deploy a malicious contract that tries to reenter
        ReentrancyAttacker attacker = new ReentrancyAttacker(address(escrow));
        
        // Create agreement where payee is the attacker
        bytes32 attackAgreementId = keccak256("attack-agreement");
        vm.prank(payer);
        escrow.createAgreement(
            attackAgreementId,
            address(attacker),
            address(0),
            AMOUNT,
            TrustFlowEscrow.ArbitrationPolicy.NONE
        );

        vm.prank(payer);
        escrow.fund{value: AMOUNT}(attackAgreementId);

        // Store the agreement ID in the attacker
        attacker.setAgreementId(attackAgreementId);

        // Release should succeed without reentrancy
        vm.prank(payer);
        escrow.release(attackAgreementId);

        // Verify funds were transferred only once
        assertEq(address(escrow).balance, 0);
        assertEq(address(attacker).balance, AMOUNT);
        assertEq(attacker.attackCount(), 0); // Attack was blocked
    }

    // ============ View Functions Tests ============

    function test_GetAgreement_NonExistent() public view {
        bytes32 nonExistentId = keccak256("non-existent");
        TrustFlowEscrow.Agreement memory agreement = escrow.getAgreement(nonExistentId);
        assertEq(agreement.payer, address(0));
    }

    function test_GetAgreementState() public {
        _createAgreementNone();
        assertEq(uint8(escrow.getAgreementState(agreementId)), uint8(TrustFlowEscrow.AgreementState.CREATED));

        _fundAgreement();
        assertEq(uint8(escrow.getAgreementState(agreementId)), uint8(TrustFlowEscrow.AgreementState.FUNDED));

        vm.prank(payer);
        escrow.release(agreementId);
        assertEq(uint8(escrow.getAgreementState(agreementId)), uint8(TrustFlowEscrow.AgreementState.RELEASED));
    }

    // ============ Fuzz Tests ============

    function testFuzz_CreateAgreement_VariousAmounts(uint256 amount) public {
        vm.assume(amount > 0);
        
        vm.prank(payer);
        escrow.createAgreement(
            keccak256(abi.encodePacked("fuzz-", amount)),
            payee,
            address(0),
            amount,
            TrustFlowEscrow.ArbitrationPolicy.NONE
        );
    }
}

/**
 * @title ReentrancyAttacker
 * @notice Contract that attempts a reentrancy attack on release()
 */
contract ReentrancyAttacker {
    TrustFlowEscrow public escrow;
    bytes32 public agreementId;
    uint256 public attackCount;

    constructor(address _escrow) {
        escrow = TrustFlowEscrow(_escrow);
    }

    function setAgreementId(bytes32 _agreementId) external {
        agreementId = _agreementId;
    }

    receive() external payable {
        // Try to reenter release
        if (address(escrow).balance >= 1 ether) {
            attackCount++;
            // This should fail due to ReentrancyGuard
            try escrow.release(agreementId) {
                // If we get here, the attack succeeded (which is bad)
            } catch {
                // Expected: reentrancy guard blocked the attack
            }
        }
    }
}
