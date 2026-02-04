// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script, console} from "forge-std/Script.sol";
import {TrustFlowEscrow} from "../src/TrustFlowEscrow.sol";

/**
 * @title DeployTrustFlowEscrow
 * @notice Deployment script for TrustFlowEscrow contract
 * @dev Run with: forge script script/Deploy.s.sol --rpc-url http://127.0.0.1:8545 --broadcast
 */
contract DeployTrustFlowEscrow is Script {
    function setUp() public {}

    function run() public returns (TrustFlowEscrow) {
        // Get deployer private key from environment or use default Anvil key
        uint256 deployerPrivateKey = vm.envOr(
            "PRIVATE_KEY",
            uint256(0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80) // Anvil default key 0
        );

        vm.startBroadcast(deployerPrivateKey);

        TrustFlowEscrow escrow = new TrustFlowEscrow();

        console.log("===========================================");
        console.log("TrustFlowEscrow deployed successfully!");
        console.log("===========================================");
        console.log("Contract Address:", address(escrow));
        console.log("Deployer:", vm.addr(deployerPrivateKey));
        console.log("Network:", block.chainid);
        console.log("===========================================");

        vm.stopBroadcast();

        return escrow;
    }
}
