import pytest
from stacksorbit_secrets import validate_stacks_address, validate_private_key

def test_validate_stacks_address_mainnet():
    # Valid mainnet address
    assert validate_stacks_address("SP2J1BCZK8Q0CP3W4R1XX9TMKJ1N1S8QZ7K0B5N8", "mainnet") is True
    # Testnet address on mainnet should fail
    assert validate_stacks_address("ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM", "mainnet") is False
    # Short address
    assert validate_stacks_address("SP123", "mainnet") is False
    # Invalid characters (I, L, O, U are excluded in C32)
    assert validate_stacks_address("SP2J1BCZK8Q0CP3W4R1XX9TMKJ1N1S8QZ7K0B5N8I", "mainnet") is False

def test_validate_stacks_address_testnet():
    # Valid testnet address
    assert validate_stacks_address("ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM", "testnet") is True
    # Mainnet address on testnet should fail
    assert validate_stacks_address("SP2J1BCZK8Q0CP3W4R1XX9TMKJ1N1S8QZ7K0B5N8", "testnet") is False
    # Devnet should work same as testnet
    assert validate_stacks_address("ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM", "devnet") is True

def test_validate_stacks_address_generic():
    # Should work for both SP and ST if network is None
    assert validate_stacks_address("SP2J1BCZK8Q0CP3W4R1XX9TMKJ1N1S8QZ7K0B5N8") is True
    assert validate_stacks_address("ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM") is True
    # Invalid prefix
    assert validate_stacks_address("SM1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM") is False

def test_validate_stacks_address_whitespace():
    # Leading/trailing whitespace should be handled
    assert validate_stacks_address("  ST1PQHQKV0RJXZFY1DGX8MNSNYVE3VGZJSRTPGZGM  ", "testnet") is True

def test_validate_private_key():
    # Valid 64 char hex
    valid_pk = "a" * 64
    assert validate_private_key(valid_pk) is True
    # Valid 66 char hex
    valid_pk_66 = "b" * 66
    assert validate_private_key(valid_pk_66) is True
    # Invalid length
    assert validate_private_key("a" * 63) is False
    assert validate_private_key("a" * 65) is False
    assert validate_private_key("a" * 67) is False
    # Non-hex
    assert validate_private_key("g" * 64) is False
    # Placeholder should fail
    assert validate_private_key("your_private_key_here") is False
