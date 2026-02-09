// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title RepairForwarder
 * @notice Meta-tx forwarder: user signs one EIP-712 RepairAuthorization; relayer submits.
 *        User must approve this contract on the source vault (shares) before use.
 * @dev Domain: RichesReach RepairForwarder, type: RepairAuthorization
 */
contract RepairForwarder {
    bytes32 public constant REPAIR_AUTH_TYPEHASH = keccak256(
        "RepairAuthorization(address fromVault,address toVault,uint256 amountWei,uint256 deadline,uint256 nonce)"
    );
    bytes32 public constant DOMAIN_TYPEHASH = keccak256(
        "EIP712Domain(string name,string version,uint256 chainId)"
    );
    bytes32 public immutable DOMAIN_SEPARATOR;

    mapping(address => uint256) public nonces;

    event RepairExecuted(address indexed user, address fromVault, address toVault, uint256 amountWei);

    constructor() {
        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                DOMAIN_TYPEHASH,
                keccak256("RichesReach RepairForwarder"),
                keccak256("1"),
                block.chainid
            )
        );
    }

    function executeRepair(
        address user,
        address fromVault,
        address toVault,
        uint256 amountWei,
        uint256 deadline,
        uint256 nonce,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        require(block.timestamp <= deadline, "RepairForwarder: expired");
        require(nonces[user] == nonce, "RepairForwarder: bad nonce");
        nonces[user] = nonce + 1;

        bytes32 structHash = keccak256(
            abi.encode(
                REPAIR_AUTH_TYPEHASH,
                fromVault,
                toVault,
                amountWei,
                deadline,
                nonce
            )
        );
        bytes32 digest = keccak256(
            abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR, structHash)
        );
        address signer = ecrecover(digest, v, r, s);
        require(signer == user && signer != address(0), "RepairForwarder: invalid signature");

        // Pull assets from user's position into this contract (user must have approved this contract on fromVault)
        IERC4626(fromVault).withdraw(amountWei, address(this), user);

        // Approve toVault to pull the underlying asset from this contract, then deposit for user
        address underlying = IERC4626(toVault).asset();
        IERC20(underlying).approve(toVault, amountWei);
        IERC4626(toVault).deposit(amountWei, user);

        emit RepairExecuted(user, fromVault, toVault, amountWei);
    }

    function getNonce(address user) external view returns (uint256) {
        return nonces[user];
    }
}

interface IERC4626 {
    function asset() external view returns (address);
    function withdraw(uint256 assets, address receiver, address owner) external returns (uint256 shares);
    function deposit(uint256 assets, address receiver) external returns (uint256 shares);
}
