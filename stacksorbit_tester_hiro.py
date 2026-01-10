#!/usr/bin/env python3
"""
Enhanced StacksOrbit Testing Module using Hiro SDK
Comprehensive testing integration for full development lifecycle
Leverages @stacks/clarinet-sdk for Clarity 4 compatibility
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"

class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TestResult:
    name: str
    type: TestType
    status: TestStatus
    duration: float
    output: str
    error: Optional[str] = None

class StacksOrbitTester:
    """Comprehensive testing system using Hiro SDK"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.test_results: List[TestResult] = []
        self.config = self._load_test_config()
        
    def _load_test_config(self) -> Dict:
        """Load test configuration"""
        config_path = self.project_root / "stacksorbit.test.config.json"
        
        default_config = {
            "test_suites": {
                "unit": {
                    "enabled": True,
                    "timeout": 30000,
                    "parallel": False,
                    "files": ["tests/unit/**/*.test.ts", "tests/**/*.test.ts"],
                    "vitest_config": "vitest.config.enhanced.ts"
                },
                "integration": {
                    "enabled": True,
                    "timeout": 60000,
                    "parallel": False,
                    "files": ["tests/integration/**/*.test.ts"],
                    "vitest_config": "vitest.config.enhanced.ts"
                },
                "hiro": {
                    "enabled": True,
                    "timeout": 60000,
                    "parallel": False,
                    "files": ["tests/integration/hiro-api.test.ts"],
                    "vitest_config": "vitest.config.enhanced.ts"
                }
            },
            "pre_checks": {
                "clarinet_check": True,
                "hiro_sdk_check": True
            },
            "post_checks": {
                "coverage": True,
                "deployment_verification": True
            }
        }
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def run_pre_checks(self) -> Tuple[bool, List[str]]:
        """Run pre-test checks using Hiro tools"""
        issues = []
        
        print("🔍 Running pre-test checks with Hiro SDK...")
        
        # Check if contracts compile with Clarinet
        if self.config["pre_checks"]["clarinet_check"]:
            try:
                result = subprocess.run(
                    ["clarinet", "check"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode != 0:
                    issues.append("Contract compilation failed")
                    print(f"❌ Contract check failed")
                else:
                    print("✅ Contract compilation successful")
                    
            except subprocess.TimeoutExpired:
                issues.append("Contract check timed out")
                print("❌ Contract check timed out")
            except FileNotFoundError:
                issues.append("Clarinet not found")
                print("❌ Clarinet not found")
        
        # Check Hiro SDK availability
        if self.config["pre_checks"]["hiro_sdk_check"]:
            try:
                result = subprocess.run(
                    ["npm", "list", "@stacks/clarinet-sdk"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if "@stacks/clarinet-sdk" in result.stdout:
                    print("✅ Hiro Clarinet SDK available")
                else:
                    issues.append("Hiro Clarinet SDK not installed")
                    print("❌ Hiro Clarinet SDK not found")
                    
            except Exception as e:
                issues.append(f"Hiro SDK check failed: {str(e)}")
                print(f"❌ Hiro SDK check failed: {e}")
        
        # Check test files exist
        test_files = list(self.project_root.rglob("*.test.ts"))
        if not test_files:
            issues.append("No test files found")
            print("❌ No test files found")
        else:
            print(f"✅ Found {len(test_files)} test files")
            
        return len(issues) == 0, issues
    
    def run_vitest_tests(self, test_suite: str) -> List[TestResult]:
        """Run Vitest tests using Hiro SDK configuration"""
        results = []
        
        if not self.config["test_suites"][test_suite]["enabled"]:
            return results
            
        suite_config = self.config["test_suites"][test_suite]
        print(f"🧪 Running {test_suite} tests with Hiro SDK...")
        
        # Use existing npm scripts from package.json
        cmd = ["npm", "run", "test"]
        
        # Use specific test suite commands if available
        if test_suite == "hiro" and "test:hiro" in self._get_npm_scripts():
            cmd = ["npm", "run", "test:hiro"]
        elif test_suite == "dex-dimension" and "test:dex-dimension" in self._get_npm_scripts():
            cmd = ["npm", "run", "test:dex-dimension"]
        elif test_suite == "governance-dimension" and "test:governance-dimension" in self._get_npm_scripts():
            cmd = ["npm", "run", "test:governance-dimension"]
        else:
            # Use vitest directly with enhanced config
            cmd = ["npx", "vitest", "run", "--config", suite_config["vitest_config"]]
            
            # Add specific test files if configured
            if suite_config["files"]:
                cmd.extend(suite_config["files"])
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=suite_config["timeout"]
            )
            
            duration = time.time() - start_time
            status = TestStatus.PASSED if result.returncode == 0 else TestStatus.FAILED
            
            test_result = TestResult(
                name=f"vitest-{test_suite}",
                type=TestType[test_suite.upper()] if test_suite.upper() in TestType.__members__ else TestType.UNIT,
                status=status,
                duration=duration,
                output=result.stdout + result.stderr,
                error=result.stderr if result.returncode != 0 else None
            )
            
            results.append(test_result)
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            results.append(TestResult(
                name=f"vitest-{test_suite}",
                type=TestType[test_suite.upper()] if test_suite.upper() in TestType.__members__ else TestType.UNIT,
                status=TestStatus.FAILED,
                duration=duration,
                output="",
                error="Test execution timed out"
            ))
        except FileNotFoundError:
            results.append(TestResult(
                name=f"vitest-{test_suite}",
                type=TestType[test_suite.upper()] if test_suite.upper() in TestType.__members__ else TestType.UNIT,
                status=TestStatus.FAILED,
                duration=0,
                output="",
                error="npm/vitest not found"
            ))
        
        return results
    
    def _get_npm_scripts(self) -> Dict[str, str]:
        """Get available npm scripts from package.json"""
        package_json = self.project_root / "package.json"
        if package_json.exists():
            with open(package_json, 'r') as f:
                data = json.load(f)
                return data.get("scripts", {})
        return {}
    
    def run_all_tests(self) -> Dict[str, List[TestResult]]:
        """Run comprehensive test suite using Hiro SDK"""
        all_results = {}
        
        print("🚀 Starting comprehensive test suite with Hiro SDK...")
        print("=" * 60)
        
        # Run pre-checks
        pre_checks_passed, issues = self.run_pre_checks()
        if not pre_checks_passed:
            print("❌ Pre-checks failed. Aborting tests.")
            for issue in issues:
                print(f"  - {issue}")
            return all_results
        
        # Run Vitest test suites
        for suite in ["unit", "integration", "hiro"]:
            if self.config["test_suites"][suite]["enabled"]:
                suite_results = self.run_vitest_tests(suite)
                all_results[suite] = suite_results
                for result in suite_results:
                    self._print_test_result(result)
        
        # Run dimension-specific tests if available
        dimension_suites = ["dex-dimension", "governance-dimension", "oracle-dimension", "risk-dimension"]
        for suite in dimension_suites:
            if suite in self._get_npm_scripts():
                suite_results = self.run_vitest_tests(suite)
                all_results[suite] = suite_results
                for result in suite_results:
                    self._print_test_result(result)
        
        # Print summary
        self._print_test_summary(all_results)
        
        return all_results
    
    def _print_test_result(self, result: TestResult):
        """Print individual test result"""
        status_icon = {
            TestStatus.PASSED: "✅",
            TestStatus.FAILED: "❌",
            TestStatus.SKIPPED: "⏭️",
            TestStatus.RUNNING: "🔄"
        }.get(result.status, "❓")
        
        print(f"{status_icon} {result.name} ({result.duration:.2f}s)")
        
        if result.error:
            print(f"   Error: {result.error}")
    
    def _print_test_summary(self, all_results: Dict[str, List[TestResult]]):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 Test Summary (Hiro SDK)")
        print("=" * 60)
        
        total_tests = sum(len(results) for results in all_results.values())
        passed_tests = sum(1 for results in all_results.values() for result in results if result.status == TestStatus.PASSED)
        failed_tests = sum(1 for results in all_results.values() for result in results if result.status == TestStatus.FAILED)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for suite, results in all_results.items():
                for result in results:
                    if result.status == TestStatus.FAILED:
                        print(f"  - {result.name}: {result.error}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        if failed_tests == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed. Please review the issues above.")

def main():
    """Main entry point for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="StacksOrbit Testing Suite with Hiro SDK")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--suite", choices=["unit", "integration", "hiro", "dex-dimension", "governance-dimension", "oracle-dimension", "risk-dimension", "all"], default="all", help="Test suite to run")
    parser.add_argument("--hiro", action="store_true", help="Run only Hiro SDK tests")
    parser.add_argument("--coverage", action="store_true", help="Generate test coverage report")
    
    args = parser.parse_args()
    
    tester = StacksOrbitTester(args.project_root)
    
    if args.hiro:
        results = tester.run_vitest_tests("hiro")
        for result in results:
            tester._print_test_result(result)
        failed = any(r.status.value == "failed" for r in results)
        return 1 if failed else 0
    else:
        # Run all tests
        all_results = tester.run_all_tests()
        
        # Check if any tests failed
        failed_tests = 0
        for suite, results in all_results.items():
            for result in results:
                if result.status.value == "failed":
                    failed_tests += 1
        
        if args.coverage:
            print(f"\n📊 Generating Coverage Report...")
            try:
                subprocess.run(["npm", "run", "coverage"], cwd=tester.project_root, check=True)
                print("✅ Coverage report generated")
            except subprocess.CalledProcessError:
                print("⚠️  Coverage report generation failed")
        
        return 1 if failed_tests > 0 else 0

if __name__ == "__main__":
    main()
