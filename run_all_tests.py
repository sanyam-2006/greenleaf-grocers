"""
Master Test Suite Runner and Automated Test Report Generator for GreenLeaf Grocers.
Executes all unit tests across Days 1 through 7 and compiles an executive test report.
"""
import io
import os
import sys
import time
import unittest
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

TEST_MODULES = [
    "tests.test_day1",
    "tests.test_day2_auth",
    "tests.test_day3_products",
    "tests.test_day4_billing",
    "tests.test_day5_analytics",
    "tests.test_day6_charts",
    "tests.test_day7_edge_cases",
]


def run_comprehensive_test_suite():
    print("=" * 72)
    print("  GREENLEAF GROCERS - COMPREHENSIVE SYSTEM TEST SUITE RUNNER")
    print("=" * 72)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python:    {sys.version.split()[0]} ({sys.executable})")
    print(f"Modules:   {len(TEST_MODULES)} test modules")
    print("-" * 72)

    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0
    module_summaries = []

    start_time = time.time()

    for mod_name in TEST_MODULES:
        suite = unittest.defaultTestLoader.loadTestsFromName(mod_name)
        runner = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0)
        res = runner.run(suite)

        run_count = res.testsRun
        fail_count = len(res.failures)
        err_count = len(res.errors)
        skip_count = len(res.skipped)
        passed_count = run_count - fail_count - err_count - skip_count

        total_tests += run_count
        total_failures += fail_count
        total_errors += err_count
        total_skipped += skip_count

        status = "PASSED" if (fail_count == 0 and err_count == 0) else "FAILED"
        pass_pct = (passed_count / (run_count - skip_count) * 100) if (run_count - skip_count) > 0 else 100.0

        module_summaries.append({
            "module": mod_name,
            "total": run_count,
            "passed": passed_count,
            "failed": fail_count,
            "errors": err_count,
            "skipped": skip_count,
            "status": status,
            "pass_pct": pass_pct
        })

        tag = "PASSED" if status == "PASSED" else "FAILED"
        print(f"  {mod_name:<30} [{passed_count}/{run_count} Passed]  ({pass_pct:5.1f}%) -> {tag}")

    elapsed = time.time() - start_time
    overall_pass_pct = (
        ((total_tests - total_failures - total_errors - total_skipped) / (total_tests - total_skipped) * 100)
        if (total_tests - total_skipped) > 0 else 100.0
    )

    print("-" * 72)
    print(f"SUMMARY: {total_tests} Tests Run | {total_failures} Failures | {total_errors} Errors | {total_skipped} Skipped")
    print(f"Overall Pass Rate: {overall_pass_pct:.1f}% | Total Duration: {elapsed:.2f}s")
    print("=" * 72)

    # Generate Markdown Test Report
    report_path = PROJECT_ROOT / "test_report.md"
    generate_markdown_report(report_path, module_summaries, total_tests, total_failures, total_errors, total_skipped, overall_pass_pct, elapsed)
    print(f"\n[+] Comprehensive test report saved to: {report_path.name}")


def generate_markdown_report(filepath, modules, total, failures, errors, skipped, pass_rate, duration):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# GreenLeaf Grocers — Automated Test Suite Execution Report\n\n")
        f.write(f"**Execution Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"**Python Version**: {sys.version.split()[0]}  \n")
        f.write(f"**Execution Time**: {duration:.2f} seconds  \n")
        f.write(f"**Overall Pass Rate**: **{pass_rate:.1f}%**  \n\n")

        f.write("## 1. Executive Summary\n\n")
        f.write("| Total Tests | Passed | Failures | Errors | Skipped | Status |\n")
        f.write("| :---: | :---: | :---: | :---: | :---: | :---: |\n")
        status_badge = "✅ PASSED" if (failures == 0 and errors == 0) else "❌ FAILED"
        f.write(f"| {total} | {total - failures - errors - skipped} | {failures} | {errors} | {skipped} | **{status_badge}** |\n\n")

        f.write("## 2. Module Breakdown\n\n")
        f.write("| Module | Test File | Tests Run | Passed | Failed | Errors | Pass Rate |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: |\n")
        for m in modules:
            f.write(f"| `{m['module']}` | `{m['module'].replace('.', '/')}.py` | {m['total']} | {m['passed']} | {m['failed']} | {m['errors']} | {m['pass_pct']:.1f}% |\n")

        f.write("\n## 3. Scope of Testing\n\n")
        f.write("- **Day 1**: Database Schema integrity, table constraints, model relationships, and synthetic seed data verification.\n")
        f.write("- **Day 2**: Authentication lifecycle, password hashing, session cookies, and RBAC decorator enforcement.\n")
        f.write("- **Day 3**: Product CRUD operations, live search, multi-category filters, and CSV bulk import/export.\n")
        f.write("- **Day 4**: Point of Sale (POS) checkout engine, atomic stock decrement transactions, discounts, and printable receipt invoices.\n")
        f.write("- **Day 5**: Pandas data analytics calculations, 5 core business KPIs, inventory velocity, and department revenue distributions.\n")
        f.write("- **Day 6**: Interactive Chart.js visual canvas rendering, client-side view toggles (Revenue vs. Quantity), and reporting APIs.\n")
        f.write("- **Day 7**: Edge-case input validation, negative values rejection, overselling safeguards, and supplier directory management.\n")


if __name__ == "__main__":
    run_comprehensive_test_suite()