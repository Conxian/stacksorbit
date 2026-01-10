#!/usr/bin/env python3
"""
Enhanced StacksOrbit Testing Module
Comprehensive testing integration for full development lifecycle
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
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
    """Comprehensive testing system for StacksOrbit"""
    
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
                    "files": ["tests/unit/**/*.test.ts", "tests/**/*.test.ts"]
                },
                "integration": {
                    "enabled": True,
                    "timeout": 60000,
                    "parallel": False,
                    "files": ["tests/integration/**/*.test.ts"]
                },
                "e2e": {
                    "enabled": True,
                    "timeout": 120000,
                    "parallel": False,
                    "files": ["tests/e2e/**/*.test.ts"]
                },
                "performance": {
                    "enabled": False,
                    "timeout": 300000,
                    "parallel": False,
                    "files": ["tests/performance/**/*.test.ts"]
                },
                "security": {
                    "enabled": True,
                    "timeout": 90000,
                    "parallel": False,
                    "files": ["tests/security/**/*.test.ts"]
                }
            },
            "pre_checks": {
                "clarinet_check": True,
                "contract_analysis": True,
                "dependency_check": True
            },
            "post_checks": {
                "coverage": True,
                "deployment_verification": True,
                "security_scan": True
            }
        }
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def run_pre_checks(self) -> Tuple[bool, List[str]]:
        """Run pre-test checks"""
        issues = []
        
        print("🔍 Running pre-test checks...")
        
        # Check if contracts compile
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
                    print(f"❌ Contract check failed: {result.stderr}")
                else:
                    print("✅ Contract compilation successful")
                    
            except subprocess.TimeoutExpired:
                issues.append("Contract check timed out")
                print("❌ Contract check timed out")
            except FileNotFoundError:
                issues.append("Clarinet not found")
                print("❌ Clarinet not found")
        
        # Check test files exist
        test_files = list(self.project_root.rglob("*.test.ts"))
        if not test_files:
            issues.append("No test files found")
            print("❌ No test files found")
        else:
            print(f"✅ Found {len(test_files)} test files")
            
        return len(issues) == 0, issues
    
    def run_clarinet_tests(self) -> TestResult:
        """Run Clarinet contract tests"""
        test_name = "clarinet-contract-tests"
        start_time = time.time()
        
        try:
            print("🧪 Running Clarinet contract tests...")
            
            result = subprocess.run(
                ["clarinet", "--version"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Check if clarinet supports test command
            if "test" not in result.stdout:
                # Try running contract check instead
                result = subprocess.run(
                    ["clarinet", "check"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                duration = time.time() - start_time
                status = TestStatus.PASSED if result.returncode == 0 else TestStatus.FAILED
                
                return TestResult(
                    name="clarinet-contract-check",
                    type=TestType.UNIT,
                    status=status,
                    duration=duration,
                    output=result.stdout + result.stderr,
                    error=result.stderr if result.returncode != 0 else None
                )
            else:
                # Run actual tests
                result = subprocess.run(
                    ["clarinet", "test"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                duration = time.time() - start_time
                status = TestStatus.PASSED if result.returncode == 0 else TestStatus.FAILED
                
                return TestResult(
                    name="clarinet-contract-tests",
                    type=TestType.UNIT,
                    status=status,
                    duration=duration,
                    output=result.stdout + result.stderr,
                    error=result.stderr if result.returncode != 0 else None
                )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return TestResult(
                name=test_name,
                type=TestType.UNIT,
                status=TestStatus.FAILED,
                duration=duration,
                output="",
                error="Test execution timed out"
            )
    
    def run_vitest_tests(self, test_suite: str) -> List[TestResult]:
        """Run Vitest tests for a specific suite"""
        results = []
        
        if not self.config["test_suites"][test_suite]["enabled"]:
            return results
            
        suite_config = self.config["test_suites"][test_suite]
        print(f"🧪 Running {test_suite} tests...")
        
        # Build vitest command
        cmd = ["npm", "test"]
        
        if test_suite == "unit":
            cmd.extend(["--run", "--config", "vitest.config.enhanced.ts"])
        elif test_suite == "integration":
            cmd.extend(["--run", "--config", "vitest.config.enhanced.ts"])
        elif test_suite == "e2e":
            cmd.extend(["--run", "--config", "vitest.config.enhanced.ts"])
        elif test_suite == "performance":
            cmd.extend(["--run", "--config", "vitest.config.enhanced.ts"])
        elif test_suite == "security":
            cmd.extend(["--run", "--config", "vitest.config.enhanced.ts"])
        
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
            
            # Parse results to extract individual test results
            test_result = TestResult(
                name=f"vitest-{test_suite}",
                type=TestType[test_suite.upper()],
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
                type=TestType[test_suite.upper()],
                status=TestStatus.FAILED,
                duration=duration,
                output="",
                error="Test execution timed out"
            ))
        except FileNotFoundError:
            results.append(TestResult(
                name=f"vitest-{test_suite}",
                type=TestType[test_suite.upper()],
                status=TestStatus.FAILED,
                duration=0,
                output="",
                error="npm not found"
            ))
        
        return results
    
    def run_contract_analysis(self) -> TestResult:
        """Run contract analysis tests"""
        test_name = "contract-analysis"
        start_time = time.time()
        
        try:
            print("🔍 Running contract analysis...")
            
            # Use StacksOrbit's contract analysis
            sys.path.append(str(self.project_root.parent / "stacksorbit"))
            from enhanced_auto_detector import EnhancedAutoDetector
            
            detector = EnhancedAutoDetector(str(self.project_root))
            analysis_result = detector.analyze_contracts()
            
            duration = time.time() - start_time
            
            # Check for critical issues
            critical_issues = []
            for issue in analysis_result.get("issues", []):
                if issue.get("severity") == "critical":
                    critical_issues.append(issue)
            
            status = TestStatus.FAILED if critical_issues else TestStatus.PASSED
            
            output = json.dumps(analysis_result, indent=2)
            error = f"Found {len(critical_issues)} critical issues" if critical_issues else None
            
            return TestResult(
                name=test_name,
                type=TestType.SECURITY,
                status=status,
                duration=duration,
                output=output,
                error=error
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name=test_name,
                type=TestType.SECURITY,
                status=TestStatus.FAILED,
                duration=duration,
                output="",
                error=str(e)
            )
    
    def run_deployment_verification(self) -> TestResult:
        """Run deployment verification tests"""
        test_name = "deployment-verification"
        start_time = time.time()
        
        try:
            print("🚀 Running deployment verification...")
            
            # Use StacksOrbit's deployment verifier
            sys.path.append(str(self.project_root.parent / "stacksorbit"))
            from deployment_verifier import DeploymentVerifier
            
            verifier = DeploymentVerifier(str(self.project_root))
            verification_result = verifier.verify_deployment()
            
            duration = time.time() - start_time
            status = TestStatus.PASSED if verification_result.get("success") else TestStatus.FAILED
            
            output = json.dumps(verification_result, indent=2)
            error = verification_result.get("error")
            
            return TestResult(
                name=test_name,
                type=TestType.INTEGRATION,
                status=status,
                duration=duration,
                output=output,
                error=error
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name=test_name,
                type=TestType.INTEGRATION,
                status=TestStatus.FAILED,
                duration=duration,
                output="",
                error=str(e)
            )
    
    def run_all_tests(self) -> Dict[str, List[TestResult]]:
        """Run comprehensive test suite"""
        all_results = {}
        
        print("🚀 Starting comprehensive test suite...")
        print("=" * 60)
        
        # Run pre-checks
        pre_checks_passed, issues = self.run_pre_checks()
        if not pre_checks_passed:
            print("❌ Pre-checks failed. Aborting tests.")
            for issue in issues:
                print(f"  - {issue}")
            return all_results
        
        # Run Clarinet tests
        clarinet_result = self.run_clarinet_tests()
        all_results["clarinet"] = [clarinet_result]
        self._print_test_result(clarinet_result)
        
        # Run Vitest test suites
        for suite in ["unit", "integration", "security"]:
            if self.config["test_suites"][suite]["enabled"]:
                suite_results = self.run_vitest_tests(suite)
                all_results[suite] = suite_results
                for result in suite_results:
                    self._print_test_result(result)
        
        # Run contract analysis
        if self.config["pre_checks"]["contract_analysis"]:
            analysis_result = self.run_contract_analysis()
            all_results["analysis"] = [analysis_result]
            self._print_test_result(analysis_result)
        
        # Run deployment verification
        if self.config["post_checks"]["deployment_verification"]:
            deploy_result = self.run_deployment_verification()
            all_results["deployment"] = [deploy_result]
            self._print_test_result(deploy_result)
        
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
        print("📊 Test Summary")
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
    
    parser = argparse.ArgumentParser(description="StacksOrbit Testing Suite")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--suite", choices=["unit", "integration", "e2e", "performance", "security", "all"], default="all", help="Test suite to run")
    parser.add_argument("--clarinet", action="store_true", help="Run only Clarinet tests")
    parser.add_argument("--vitest", action="store_true", help="Run only Vitest tests")
    parser.add_argument("--analysis", action="store_true", help="Run only contract analysis")
    parser.add_argument("--deployment", action="store_true", help="Run only deployment verification")
    
    args = parser.parse_args()
    
    tester = StacksOrbitTester(args.project_root)
    
    if args.clarinet:
        result = tester.run_clarinet_tests()
        tester._print_test_result(result)
    elif args.vitest:
        # Run specific vitest suite
        pass
    elif args.analysis:
        result = tester.run_contract_analysis()
        tester._print_test_result(result)
    elif args.deployment:
        result = tester.run_deployment_verification()
        tester._print_test_result(result)
    else:
        # Run all tests
        tester.run_all_tests()

if __name__ == "__main__":
    main()
