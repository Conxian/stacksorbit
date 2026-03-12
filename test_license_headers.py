import os

def test_license_headers():
    files_to_check = [
        "stacksorbit.py",
        "stacksorbit_gui.py",
        "stacksorbit_secrets.py",
        "stacksorbit_cli.py",
        "setup.py",
        "vitest.config.ts"
    ]

    for file in files_to_check:
        assert os.path.exists(file), f"{file} does not exist"
        with open(file, "r") as f:
            content = f.read()
            assert "Copyright (c) 2025 Anya Chain Labs" in content, f"License missing in {file}"
            assert "MIT License" in content, f"License type missing in {file}"

if __name__ == "__main__":
    test_license_headers()
    print("✅ All license headers verified!")
