"""Smart contract ABI for TrustFlowEscrow."""

TRUSTFLOW_ESCROW_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "agreementId", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "payer", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "payee", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {
                "indexed": False,
                "internalType": "enum TrustFlowEscrow.ArbitrationPolicy",
                "name": "policy",
                "type": "uint8",
            },
            {"indexed": False, "internalType": "address", "name": "arbitrator", "type": "address"},
        ],
        "name": "AgreementCreated",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "agreementId", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "openedBy", "type": "address"},
        ],
        "name": "DisputeOpened",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "agreementId", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "payer", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "PaymentFunded",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "agreementId", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "payer", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "PaymentRefunded",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "agreementId", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "payee", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "PaymentReleased",
        "type": "event",
    },
]
