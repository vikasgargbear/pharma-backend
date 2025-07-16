#!/usr/bin/env python3
"""
Enterprise Test Suite Runner
===========================
Orchestrates the execution of all test categories with proper reporting,
parallel execution, and CI/CD integration.
"""

import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import concurrent.futures

# Add tests directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_suite_config import Environment, ENVIRONMENTS, TEST_CATEGORIES, TestMetrics


class EnterpriseTestRunner:
    """Main test runner for enterprise test suite"""
    
    def __init__(self, environment: Environment = Environment.LOCAL, 
                 parallel: bool = True, verbose: bool = False):
        self.environment = environment
        self.parallel = parallel
        self.verbose = verbose
        self.results_dir = Path("test_results")
        self.results_dir.mkdir(exist_ok=True)
        self.metrics = TestMetrics()
        self.test_results = {}
        
    def run_test_module(self, module_name: str, marks: Optional[str] = None) -> Dict[str, Any]:
        """Run a specific test module with pytest"""
        cmd = [
            "python", "-m", "pytest",
            f"tests/{module_name}",
            "-v" if self.verbose else "-q",
            "--json-report",
            f"--json-report-file={self.results_dir}/{module_name}.json",
            f"--junit-xml={self.results_dir}/{module_name}.xml",
            "--tb=short"
        ]
        
        if marks:
            cmd.extend(["-m", marks])
        
        # Add environment variable
        env = os.environ.copy()
        env["TEST_ENV"] = self.environment.value
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=600  # 10 minute timeout per module
            )
            
            duration = time.time() - start_time
            
            # Parse results
            json_report_path = self.results_dir / f"{module_name}.json"
            if json_report_path.exists():
                with open(json_report_path, "r") as f:
                    json_report = json.load(f)
                
                return {
                    "module": module_name,
                    "duration": duration,
                    "passed": json_report["summary"].get("passed", 0),
                    "failed": json_report["summary"].get("failed", 0),
                    "skipped": json_report["summary"].get("skipped", 0),
                    "total": json_report["summary"].get("total", 0),
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                # Fallback if JSON report not generated
                return {
                    "module": module_name,
                    "duration": duration,
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "error": "JSON report not generated"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "module": module_name,
                "duration": 600,
                "error": "Test execution timeout",
                "exit_code": -1
            }
        except Exception as e:
            return {
                "module": module_name,
                "duration": time.time() - start_time,
                "error": str(e),
                "exit_code": -1
            }
    
    def run_category(self, category: str, patterns: List[str]) -> Dict[str, Any]:
        """Run all tests in a category"""
        print(f"\n{'='*60}")
        print(f"Running {category.upper()} tests...")
        print(f"{'='*60}")
        
        category_results = {
            "category": category,
            "modules": [],
            "total_duration": 0,
            "total_passed": 0,
            "total_failed": 0,
            "total_skipped": 0
        }
        
        # Determine which test modules to run based on patterns
        test_modules = []
        
        if category == "smoke":
            test_modules = ["test_authentication.py", "test_core_business.py"]
        elif category == "authentication":
            test_modules = ["test_authentication.py"]
        elif category == "core_business":
            test_modules = ["test_core_business.py"]
        elif category == "financial":
            test_modules = ["test_financial.py"]
        elif category == "integration":
            test_modules = ["test_integration.py"]
        elif category == "security":
            test_modules = ["test_security.py"]
        elif category == "performance":
            test_modules = ["test_performance.py"]
        else:
            # Run all tests
            test_modules = [
                "test_authentication.py",
                "test_core_business.py",
                "test_financial.py",
                "test_integration.py",
                "test_security.py",
                "test_performance.py"
            ]
        
        # Run tests
        if self.parallel and len(test_modules) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                future_to_module = {
                    executor.submit(self.run_test_module, module): module 
                    for module in test_modules
                }
                
                for future in concurrent.futures.as_completed(future_to_module):
                    result = future.result()
                    category_results["modules"].append(result)
                    self._update_category_stats(category_results, result)
        else:
            for module in test_modules:
                result = self.run_test_module(module)
                category_results["modules"].append(result)
                self._update_category_stats(category_results, result)
        
        return category_results
    
    def _update_category_stats(self, category_results: Dict[str, Any], 
                               module_result: Dict[str, Any]):
        """Update category statistics with module results"""
        category_results["total_duration"] += module_result.get("duration", 0)
        category_results["total_passed"] += module_result.get("passed", 0)
        category_results["total_failed"] += module_result.get("failed", 0)
        category_results["total_skipped"] += module_result.get("skipped", 0)
    
    def run_all_tests(self, categories: Optional[List[str]] = None):
        """Run all test categories"""
        self.metrics.start_suite()
        
        if not categories:
            categories = list(TEST_CATEGORIES.keys())
        
        print(f"\n{'*'*60}")
        print(f"ENTERPRISE TEST SUITE - {self.environment.value.upper()}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'*'*60}")
        
        all_results = []
        
        for category in categories:
            if category in TEST_CATEGORIES:
                result = self.run_category(category, TEST_CATEGORIES[category])
                all_results.append(result)
                
                # Update metrics
                for module in result["modules"]:
                    if "passed" in module:
                        for _ in range(module["passed"]):
                            self.metrics.record_test(f"{category}_{module['module']}", 
                                                   "passed", 0.1)
                    if "failed" in module:
                        for _ in range(module["failed"]):
                            self.metrics.record_test(f"{category}_{module['module']}", 
                                                   "failed", 0.1, "Test failed")
        
        self.metrics.end_suite()
        
        # Generate reports
        self._generate_summary_report(all_results)
        self._generate_html_report(all_results)
        self._generate_junit_report(all_results)
        
        # Determine exit code
        total_failed = sum(r["total_failed"] for r in all_results)
        return 0 if total_failed == 0 else 1
    
    def _generate_summary_report(self, results: List[Dict[str, Any]]):
        """Generate summary report to console and file"""
        print(f"\n{'='*60}")
        print("TEST EXECUTION SUMMARY")
        print(f"{'='*60}")
        
        total_passed = sum(r["total_passed"] for r in results)
        total_failed = sum(r["total_failed"] for r in results)
        total_skipped = sum(r["total_skipped"] for r in results)
        total_tests = total_passed + total_failed + total_skipped
        total_duration = sum(r["total_duration"] for r in results)
        
        print(f"\nEnvironment: {self.environment.value.upper()}")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"\nTest Results:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {total_passed} ({total_passed/total_tests*100:.1f}%)")
        print(f"  Failed: {total_failed} ({total_failed/total_tests*100:.1f}%)")
        print(f"  Skipped: {total_skipped} ({total_skipped/total_tests*100:.1f}%)")
        
        print(f"\nCategory Breakdown:")
        for result in results:
            print(f"\n  {result['category'].upper()}:")
            print(f"    Duration: {result['total_duration']:.2f}s")
            print(f"    Passed: {result['total_passed']}")
            print(f"    Failed: {result['total_failed']}")
            print(f"    Skipped: {result['total_skipped']}")
        
        # Save to file
        summary = {
            "environment": self.environment.value,
            "timestamp": datetime.now().isoformat(),
            "total_duration": total_duration,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_skipped": total_skipped,
            "pass_rate": total_passed / total_tests * 100 if total_tests > 0 else 0,
            "categories": results
        }
        
        with open(self.results_dir / "test_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        # Generate metrics report
        metrics_report = self.metrics.generate_report()
        with open(self.results_dir / "test_metrics.json", "w") as f:
            json.dump(metrics_report, f, indent=2)
    
    def _generate_html_report(self, results: List[Dict[str, Any]]):
        """Generate HTML report"""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Enterprise Test Report - {timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; }}
        .summary {{ background-color: #ecf0f1; padding: 15px; margin: 20px 0; }}
        .category {{ margin: 20px 0; border: 1px solid #ddd; padding: 15px; }}
        .passed {{ color: #27ae60; font-weight: bold; }}
        .failed {{ color: #e74c3c; font-weight: bold; }}
        .skipped {{ color: #f39c12; font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #34495e; color: white; }}
        .progress-bar {{ width: 100%; height: 20px; background-color: #ddd; }}
        .progress-fill {{ height: 100%; background-color: #27ae60; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Enterprise Test Report</h1>
        <p>Environment: {environment} | Generated: {timestamp}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Total Tests</td>
                <td>{total_tests}</td>
            </tr>
            <tr>
                <td>Passed</td>
                <td class="passed">{total_passed} ({pass_rate:.1f}%)</td>
            </tr>
            <tr>
                <td>Failed</td>
                <td class="failed">{total_failed} ({fail_rate:.1f}%)</td>
            </tr>
            <tr>
                <td>Skipped</td>
                <td class="skipped">{total_skipped}</td>
            </tr>
            <tr>
                <td>Duration</td>
                <td>{duration:.2f} seconds</td>
            </tr>
        </table>
        
        <h3>Pass Rate</h3>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {pass_rate}%"></div>
        </div>
    </div>
    
    {category_sections}
    
    <div class="footer">
        <p>Generated by Enterprise Test Suite</p>
    </div>
</body>
</html>
        """
        
        # Calculate totals
        total_passed = sum(r["total_passed"] for r in results)
        total_failed = sum(r["total_failed"] for r in results)
        total_skipped = sum(r["total_skipped"] for r in results)
        total_tests = total_passed + total_failed + total_skipped
        total_duration = sum(r["total_duration"] for r in results)
        
        # Generate category sections
        category_sections = ""
        for result in results:
            category_html = f"""
    <div class="category">
        <h2>{result['category'].upper()}</h2>
        <table>
            <tr>
                <th>Module</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Skipped</th>
                <th>Duration</th>
            </tr>
            """
            
            for module in result.get("modules", []):
                if "passed" in module:
                    category_html += f"""
            <tr>
                <td>{module['module']}</td>
                <td class="passed">{module.get('passed', 0)}</td>
                <td class="failed">{module.get('failed', 0)}</td>
                <td class="skipped">{module.get('skipped', 0)}</td>
                <td>{module.get('duration', 0):.2f}s</td>
            </tr>
                    """
            
            category_html += """
        </table>
    </div>
            """
            category_sections += category_html
        
        # Fill template
        html_content = html_template.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            environment=self.environment.value.upper(),
            total_tests=total_tests,
            total_passed=total_passed,
            total_failed=total_failed,
            total_skipped=total_skipped,
            pass_rate=total_passed / total_tests * 100 if total_tests > 0 else 0,
            fail_rate=total_failed / total_tests * 100 if total_tests > 0 else 0,
            duration=total_duration,
            category_sections=category_sections
        )
        
        with open(self.results_dir / "test_report.html", "w") as f:
            f.write(html_content)
    
    def _generate_junit_report(self, results: List[Dict[str, Any]]):
        """Consolidate JUnit XML reports for CI/CD integration"""
        # This is handled by pytest's junit-xml output
        # Additional consolidation can be done here if needed
        pass


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Enterprise Test Suite Runner for Pharmaceutical API"
    )
    
    parser.add_argument(
        "--env", 
        choices=["local", "staging", "production"],
        default="local",
        help="Test environment"
    )
    
    parser.add_argument(
        "--category",
        choices=list(TEST_CATEGORIES.keys()) + ["all"],
        nargs="+",
        default=["all"],
        help="Test categories to run"
    )
    
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Disable parallel test execution"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only smoke tests"
    )
    
    args = parser.parse_args()
    
    # Determine environment
    env_map = {
        "local": Environment.LOCAL,
        "staging": Environment.STAGING,
        "production": Environment.PRODUCTION
    }
    environment = env_map[args.env]
    
    # Determine categories
    if args.quick:
        categories = ["smoke"]
    elif "all" in args.category:
        categories = None  # Run all
    else:
        categories = args.category
    
    # Create runner
    runner = EnterpriseTestRunner(
        environment=environment,
        parallel=not args.no_parallel,
        verbose=args.verbose
    )
    
    # Run tests
    exit_code = runner.run_all_tests(categories)
    
    print(f"\n{'='*60}")
    print(f"Test reports generated in: {runner.results_dir}")
    print(f"  - HTML Report: test_report.html")
    print(f"  - JSON Summary: test_summary.json")
    print(f"  - Test Metrics: test_metrics.json")
    print(f"{'='*60}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()