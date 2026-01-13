# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright (c) 2025 ScyllaDB

"""CLI entry point for test case linting."""

import functools
import multiprocessing
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click

from utils.lint_test_cases.models import TestCaseAnalysis
from utils.lint_test_cases.analyzer import TestCaseAnalyzer


def _worker_process_file(
    file_path: Path, analyzer: TestCaseAnalyzer
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Worker function to process a single test file.

    This function is designed to be called by multiprocessing.Pool and must be
    at module level (not a method) to be picklable.

    Args:
        file_path: Path to test case file
        analyzer: TestCaseAnalyzer instance to use

    Returns:
        Tuple of (exit_code, failures)
    """
    try:
        exit_code, failures = analyzer.run_tests_for_file(file_path, verbose=True)
        return exit_code, failures
    except Exception as e:  # noqa: BLE001
        # If something goes wrong, return error info
        error_msg = f"Worker process error: {str(e)}\n{traceback.format_exc()}"
        failure_info = {"file": str(file_path), "config": "process-error", "output": [error_msg]}
        return 1, [failure_info]


def _worker_analyze_file(
    file_path: Path, analyzer: TestCaseAnalyzer
) -> Tuple[Path, TestCaseAnalysis]:
    """
    Worker function to analyze a single test file.

    Args:
        file_path: Path to test case file
        analyzer: TestCaseAnalyzer instance to use

    Returns:
        Tuple of (file_path, analysis_result)
    """
    try:
        analysis = analyzer.analyze_file(file_path)
        return file_path, analysis
    except Exception as e:  # noqa: BLE001
        # If something goes wrong, create a minimal analysis result
        error_analysis = TestCaseAnalysis(
            file_path=file_path, backends=set(), reason=f"Analysis error: {str(e)}"
        )
        return file_path, error_analysis


def _display_test_failure(failure: Dict[str, Any], file_path: Path) -> None:
    """Display a test failure with details."""
    click.echo(f"\n{'=' * 60}")
    click.secho(
        f"❌ {failure.get('file', file_path)} - {failure.get('config', 'unknown')}",
        fg="red",
        bold=True,
    )
    click.echo(f"{'=' * 60}")

    # Show output
    for line in failure.get("output", []):
        click.echo(line)
    click.echo("")  # Empty line after failure details


def _display_failure_summary(all_failures: List[Dict[str, Any]]) -> None:
    """Display a summary of all test failures."""
    click.echo(f"\n{'=' * 70}")
    click.secho("FAILURE SUMMARY:", fg="red", bold=True)
    click.echo(f"{'=' * 70}")

    for i, failure in enumerate(all_failures, 1):
        click.secho(f"\n{i}. {failure['file']} - {failure['config']}", fg="red", bold=True)

        # Find and display the error message (last non-empty line or exception)
        error_lines = [line for line in failure["output"] if line.strip()]
        if error_lines:
            # Try to find the actual error message
            for line in reversed(error_lines):
                if any(keyword in line for keyword in ["Error:", "Exception:", "Failed", "ERROR"]):
                    click.echo(f"   Error: {line.strip()}")
                    break
            else:
                # If no error keyword found, show last line
                click.echo(f"   {error_lines[-1].strip()}")

    click.echo(f"\n{'=' * 70}")
    click.secho(f"Total failures: {len(all_failures)}", fg="red", bold=True)
    click.echo(f"{'=' * 70}")


def _process_tests(
    analyzer: TestCaseAnalyzer, test_cases: List[Path], workers: int = 1
) -> Tuple[int, List[Dict[str, Any]]]:
    """Process tests either sequentially or in parallel based on workers count."""
    all_failures: List[Dict[str, Any]] = []
    worker_fn = functools.partial(_worker_process_file, analyzer=analyzer)

    if workers == 1 or len(test_cases) == 1:
        results = map(worker_fn, test_cases)
    else:
        click.echo(f"Processing {len(test_cases)} files with {workers} workers...\n")
        pool = multiprocessing.Pool(processes=workers)
        results = pool.imap_unordered(worker_fn, test_cases)

    total_exit_code = 0
    for exit_code, failures in results:
        total_exit_code += exit_code
        all_failures.extend(failures)

    if workers > 1 and len(test_cases) > 1:
        pool.close()
        pool.join()

    return total_exit_code, all_failures


def _run_test_mode(
    analyzer: TestCaseAnalyzer, test_cases: List[Path], workers: Optional[int]
) -> int:
    """Run test validation mode."""
    # Determine number of workers
    if workers is None:
        workers = multiprocessing.cpu_count()

    # Process tests (function handles sequential vs parallel internally)
    total_exit_code, all_failures = _process_tests(analyzer, test_cases, workers)

    # Display results
    click.echo(f"\n{'=' * 70}")
    if total_exit_code == 0:
        click.secho("✅ All tests passed!", fg="green", bold=True)
    else:
        click.secho(f"❌ Tests failed: {total_exit_code}", fg="red", bold=True)
        if all_failures:
            _display_failure_summary(all_failures)

    return total_exit_code


def _run_group_mode(analyzer: TestCaseAnalyzer, test_cases: List[Path]) -> None:
    """Run grouping mode to show test cases grouped by backend."""
    grouped = analyzer.group_by_backend_config(test_cases)

    for config_key, config_files in grouped.items():
        click.echo(f"\n{config_key}:")
        for file in config_files:
            click.echo(f"  - {file.relative_to(analyzer.test_cases_dir)}")


def _display_analysis_result(
    file_path: Path,
    analysis: TestCaseAnalysis,
    analyzer: TestCaseAnalyzer,
    verbose: bool,
) -> None:
    """Display analysis result for a single file."""
    # Get relative path for display
    try:
        rel_path = file_path.resolve().relative_to(analyzer.test_cases_dir)
    except ValueError:
        rel_path = file_path

    click.echo(f"\n{rel_path}")
    click.echo(f"  Backends: {', '.join(b.value for b in analysis.backends)}")

    if verbose:
        if analysis.dc_count:
            click.echo(f"  DC Count: {analysis.dc_count}")
        if analysis.explicit_backend:
            click.echo(f"  Explicit Backend: {analysis.explicit_backend.value}")
        click.echo(f"  Reason: {analysis.reason}")

        configs = analyzer.get_backend_configs(analysis)
        for config in configs:
            click.echo(f"\n  Config: {config.description}")
            click.echo(f"    Backend: {config.backend.value}")


def _run_analysis_mode(
    analyzer: TestCaseAnalyzer,
    test_cases: List[Path],
    workers: Optional[int],
    verbose: bool,
) -> None:
    """Run analysis mode to show backend recommendations."""
    # Determine number of workers for analysis
    if workers is None:
        workers = multiprocessing.cpu_count()

    # Use parallel processing for analysis if multiple files and workers > 1
    if workers > 1 and len(test_cases) > 1:
        click.echo(f"Analyzing {len(test_cases)} files with {workers} workers...")
        click.echo("")  # Empty line for better readability

        with multiprocessing.Pool(processes=workers) as pool:
            # Display results as they complete
            for file_path, analysis in pool.imap_unordered(functools.partial(_worker_analyze_file, analyzer=analyzer), test_cases):
                _display_analysis_result(file_path, analysis, analyzer, verbose)
    else:
        # Sequential processing for single file or workers=1
        for test_case in test_cases:
            analysis = analyzer.analyze_file(test_case)
            _display_analysis_result(test_case, analysis, analyzer, verbose)


@click.command("lint-yamls", help="Test yaml in test-cases directory")
@click.argument("files", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option("--group", is_flag=True, help="Group test cases by backend configuration")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed analysis")
@click.option(
    "--run", "run_tests", is_flag=True, help="Run YAML validation tests for the analyzed files"
)
@click.option(
    "--test",
    "run_tests_alias",
    is_flag=True,
    help="Alias for --run (run YAML validation tests)",
)
@click.option(
    "--workers",
    "-j",
    type=int,
    default=None,
    help="Number of parallel workers (default: CPU count)",
)
def main(files, group, verbose, run_tests, run_tests_alias, workers):
    """Analyze test case files and determine appropriate backends.

    FILES: Test case files to analyze (default: all in test-cases/)
    """
    analyzer = TestCaseAnalyzer()

    if files:
        test_cases = list(files)
    else:
        test_cases = analyzer.find_all_test_cases()

    # Handle test execution
    if run_tests or run_tests_alias:
        exit_code = _run_test_mode(analyzer, test_cases, workers)
        sys.exit(exit_code)
    elif group:
        _run_group_mode(analyzer, test_cases)
    else:
        _run_analysis_mode(analyzer, test_cases, workers, verbose)
