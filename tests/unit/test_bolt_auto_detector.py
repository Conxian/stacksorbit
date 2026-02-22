import pytest
import re
from pathlib import Path
from unittest.mock import MagicMock, patch
from enhanced_auto_detector import GenericStacksAutoDetector

def test_sorting_priority_logic():
    detector = GenericStacksAutoDetector()

    # Priority order snippet for reference:
    # 1. traits, interface
    # 2. utils, helper, lib
    # 3. core
    # ...

    contracts = [
        {"name": "core-contract"},
        {"name": "my-utils"},
        {"name": "sip-009-nft-trait"},
        {"name": "test-mock"},
    ]

    sorted_contracts = detector._sort_contracts_by_generic_dependencies(contracts)

    names = [c["name"] for c in sorted_contracts]
    # Expected order: trait (sip-009), utils, core, test
    assert names == ["sip-009-nft-trait", "my-utils", "core-contract", "test-mock"]

def test_multiple_keyword_matches():
    detector = GenericStacksAutoDetector()

    # "math-lib" matches "math" and "lib"
    # In PRIORITY_ORDER:
    # ... "library", "lib", "math", "string" ...
    # "lib" comes before "math"

    contracts = [
        {"name": "math-lib"},
        {"name": "just-math"},
    ]

    # lib is at index ~12, math at index ~13
    # both should be prioritized similarly, but let's check
    p_math_lib = detector._sort_contracts_by_generic_dependencies([{"name": "math-lib"}])[0]
    p_math = detector._sort_contracts_by_generic_dependencies([{"name": "just-math"}])[0]

    # Actually _sort_contracts_by_generic_dependencies returns the list sorted.
    # We want to check if the priority assigned is correct.

    # Verify regex matches correctly
    matches = detector._priority_re.findall("math-lib")
    assert "math" in matches
    assert "lib" in matches

    idx_math = detector._priority_map["math"]
    idx_lib = detector._priority_map["lib"]
    assert idx_lib < idx_math

def test_project_files_cache_is_dict():
    detector = GenericStacksAutoDetector()
    cache_key = "test_dir"

    # Mock scandir to avoid real FS access
    with patch("os.scandir") as mock_scandir:
        mock_it = MagicMock()
        mock_entry = MagicMock()
        mock_entry.name = "test.clar"
        mock_entry.path = "test_dir/test.clar"
        mock_entry.is_dir.return_value = False
        mock_entry.is_file.return_value = True
        mock_entry.stat.return_value.st_mtime = 12345
        mock_entry.stat.return_value.st_size = 100

        mock_it.__enter__.return_value = [mock_entry]
        mock_scandir.return_value = mock_it

        detector._scan_project_files(Path("test_dir"))

        assert isinstance(detector.project_files_cache[cache_key], dict)
        assert "test.clar" in detector.project_files_cache[cache_key]
        assert detector.project_files_cache[cache_key]["test.clar"]["mtime"] == 12345

def test_stat_avoidance_in_clarinet_toml():
    detector = GenericStacksAutoDetector()
    directory = Path("test_project")
    cache_key = str(directory)

    detector.project_files_cache[cache_key] = {
        "contracts/my-contract.clar": {
            "mtime": 9999,
            "size": 500
        }
    }

    # Mock Clarinet.toml content
    toml_content = """
    [contracts.my-contract]
    path = "contracts/my-contract.clar"
    """

    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", MagicMock()):
            with patch("tomllib.load", return_value={
                "contracts": {
                    "my-contract": {"path": "contracts/my-contract.clar"}
                }
            }):
                # Mock stat to ensure it's NOT called for the contract
                with patch("pathlib.Path.stat") as mock_stat:
                    contracts = detector._parse_generic_clarinet_toml(directory)

                    assert len(contracts) == 1
                    assert contracts[0]["modified"] == 9999
                    assert contracts[0]["size"] == 500

                    # mock_stat should NOT have been called for the contract file
                    # It might be called for Clarinet.toml though if we didn't cache that
                    # But in our implementation, we retrieve metadata for 'contract_path'

                    # Filter calls to check if any call was for the contract file
                    contract_stat_calls = [c for c in mock_stat.call_args_list if "my-contract.clar" in str(c)]
                    assert len(contract_stat_calls) == 0
