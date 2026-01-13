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

"""Test case analyzer for determining appropriate backends."""

import logging
import os
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
import yaml

from sdcm.sct_config import SCTConfiguration

from utils.lint_test_cases.backends.aws import AWSBackend
from utils.lint_test_cases.backends.docker import DockerBackend
from utils.lint_test_cases.backends.gce import GCEBackend
from utils.lint_test_cases.backends.k8s import K8sEKSBackend, K8sGKEBackend, K8sLocalKindBackend
from utils.lint_test_cases.models import Backend, BackendConfig, TestCaseAnalysis
from utils.lint_test_cases.backends import AzureBackend, BaremetalBackend, BaseBackend


class TestCaseAnalyzer:
    """Analyzes test case YAML files to determine appropriate backends."""
    BACKENDS: List[BaseBackend] = [
        AWSBackend(),
        AzureBackend(),
        GCEBackend(),
        DockerBackend(),
        BaremetalBackend(),
        K8sLocalKindBackend(),
        K8sEKSBackend(),
        K8sGKEBackend(),
    ]

    def __init__(self, test_cases_dir: Optional[Path] = None):
        if test_cases_dir is None:
            # Try to find test-cases directory relative to this file
            script_dir = Path(__file__).resolve().parent
            project_root = script_dir.parent.parent
            self.test_cases_dir = project_root / "test-cases"
        else:
            self.test_cases_dir = test_cases_dir

        # Store project root for relative path display
        self.project_root = Path(__file__).resolve().parent.parent.parent

        # Create lookup maps for quick access
        self._backend_by_type: Dict[Backend, BaseBackend] = {
            backend.backend_type: backend for backend in self.BACKENDS
        }

    def get_backend_handler(self, backend_type: Backend) -> Optional[BaseBackend]:
        """Get the backend handler for a specific backend type."""
        return self._backend_by_type.get(backend_type)

    def link_yaml_file(
        self, backend: str, full_path: str, env: Dict[str, str]
    ) -> Tuple[bool, List[str]]:
        """
        Run YAML test validation directly using SCTConfiguration.

        Args:
            backend: Backend name (aws, gce, azure, etc.)
            full_path: Full path to the YAML test case file
            env: Environment variables to set

        Returns:
            Tuple of (error: bool, output: List[str])
        """
        output = []
        error = False
        output.append(f"---- linting: {full_path} -----")

        try:
            # Clear and set environment variables
            for key in list(os.environ.keys()):
                if key.startswith("SCT_"):
                    del os.environ[key]
            os.environ.update(env)
            os.environ["SCT_CLUSTER_BACKEND"] = backend
            os.environ["SCT_CONFIG_FILES"] = str(full_path)

            # Disable logging for this test
            logging.getLogger().handlers = []
            logging.getLogger().disabled = True

            try:
                config = SCTConfiguration()
                config.verify_configuration()
                config.check_required_files()
                output.append("✅ Configuration validated successfully")
            except Exception as exc:  # noqa: BLE001
                output.append(
                    "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                )
                error = True
        finally:
            # Restore original environment
            logging.getLogger().disabled = False

        return error, output

    def run_yaml_test_for_config(
        self,
        config: BackendConfig,
        file_path: Path,
        verbose: bool = True,
    ) -> Tuple[int, Optional[Dict[str, Any]]]:
        """
        Run YAML test validation for a specific backend configuration.

        Args:
            config: BackendConfig with backend and environment variables
            file_path: Path to the test case file
            verbose: If True, print detailed output

        Returns:
            Tuple of (exit_code, failure_info_dict or None)
        """
        # Run the test
        error, output = self.link_yaml_file(
            backend=config.backend.value,
            full_path=str(file_path.resolve()),
            env=config.env_vars,
        )

        # Get relative path from project root
        try:
            rel_path = file_path.relative_to(self.project_root)
        except ValueError:
            rel_path = file_path

        failure_info = None

        # Print output - concise for success, detailed for failure
        if verbose:
            if error:
                # Show full details for failures
                if config.description:
                    click.echo(f"\n{'=' * 60}")
                    click.echo(f"{config.description}")
                    click.echo(f"{'=' * 60}")
                click.echo(f"Testing: {rel_path}")
                for line in output:
                    click.echo(line)

                # Store failure info for summary
                failure_info = {
                    "file": str(rel_path),
                    "config": config.description or config.backend.value,
                    "output": output,
                }
            else:
                # Just one line for success
                config_desc = config.description or config.backend.value
                click.secho(f"✅ {rel_path} - {config_desc}", fg="green")

        return 1 if error else 0, failure_info

    def analyze_file(self, file_path: Path) -> TestCaseAnalysis:
        """
        Analyze a single test case file to determine appropriate backends.

        Args:
            file_path: Path to the test case YAML file

        Returns:
            TestCaseAnalysis with backend recommendations
        """
        # Resolve path to absolute
        file_path = file_path.resolve()

        backends = set()
        explicit_backend = None
        reason_parts = []

        # Load YAML content
        content = self._load_yaml(file_path)

        # Check for explicit cluster_backend in content
        if content and "cluster_backend" in content:
            backend_value = content["cluster_backend"].lower()
            try:
                explicit_backend = Backend(backend_value)
                backends.add(explicit_backend)
                reason_parts.append(f"explicit backend: {backend_value}")
            except ValueError:
                # Ignore invalid backend values
                pass

        # Get relative path for pattern matching
        try:
            filepath_str = str(file_path.relative_to(self.test_cases_dir)).lower()
        except ValueError:
            filepath_str = file_path.name.lower()

        # Check for backend-specific patterns in filename
        for backend_handler in self.BACKENDS:
            if backend_handler.matches_content(content):
                backends.add(backend_handler.backend_type)
                reason_parts.append(f"content has {backend_handler.backend_type.value} config")
            elif backend_handler.matches_filename(filepath_str):
                backends.add(backend_handler.backend_type)
                reason_parts.append(f"filename pattern: {backend_handler.backend_type.value}")

        if Backend.K8S_LOCAL_KIND in backends and (
            Backend.AWS in backends or Backend.GCE in backends
        ):
            reason_parts.append("K8S_LOCAL_KIND overridden by cloud backend config")
            backends.discard(Backend.K8S_LOCAL_KIND)

        # Check for multi-DC patterns
        dc_count = self._get_dc_count(content)
        if dc_count:
            reason_parts.append(f"multi-DC with {dc_count} DCs")

        # If no specific backend identified, assume AWS as default
        if not backends and not explicit_backend:
            backends.add(Backend.AWS)
            reason_parts.append("default backend")

        return TestCaseAnalysis(
            file_path=file_path,
            backends=backends,
            dc_count=dc_count,
            explicit_backend=explicit_backend,
            reason="; ".join(reason_parts),
        )

    def _load_yaml(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load and parse YAML file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except (OSError, yaml.YAMLError) as e:
            click.secho(f"Warning: Failed to load {file_path}: {e}", fg="yellow", err=True)
            raise

    def _get_dc_count(self, content: Optional[Dict]) -> Optional[int]:
        """Determine the number of datacenters."""
        if "n_db_nodes" in content:
            n_db_nodes = str(content["n_db_nodes"])
            if " " in n_db_nodes:
                return len(n_db_nodes.split())

        if "gce_datacenter" in content:
            gce_dc = content["gce_datacenter"]
            if isinstance(gce_dc, str) and " " in gce_dc:
                return len(gce_dc.split())
            elif isinstance(gce_dc, list):
                return len(gce_dc)

        return 1

    def get_backend_configs(self, analysis: TestCaseAnalysis) -> List[BackendConfig]:
        """
        Generate backend configurations for linting based on analysis.

        Args:
            analysis: TestCaseAnalysis result

        Returns:
            List of BackendConfig objects for running lint tests
        """
        configs = []

        for backend_type in analysis.backends:
            handler = self.get_backend_handler(backend_type)
            if handler:
                configs.extend(handler.get_configs(analysis))

        return configs

    def group_by_backend_config(
        self, test_cases: Optional[List[Path]] = None
    ) -> Dict[str, List[Path]]:
        """
        Group test cases by their backend configuration requirements.

        Args:
            test_cases: List of test case paths, or None to find all

        Returns:
            Dictionary mapping backend config keys to list of test case paths
        """
        if test_cases is None:
            test_cases = sorted(self.test_cases_dir.glob("**/*.yaml"))

        grouped: Dict[str, List[Path]] = {}

        for test_case in test_cases:
            analysis = self.analyze_file(test_case)
            configs = self.get_backend_configs(analysis)

            for config in configs:
                key = self._config_key(config)
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(test_case)

        return grouped

    def find_all_test_cases(self, pattern: str = "**/*.yaml") -> List[Path]:
        """
        Find all test case YAML files in the test-cases directory.

        Args:
            pattern: Glob pattern for finding files

        Returns:
            List of Path objects for test case files
        """
        return sorted(self.test_cases_dir.glob(pattern))

    def _config_key(self, config: BackendConfig) -> str:
        """Generate a unique key for a backend configuration."""
        parts = [config.backend.value]
        if config.multi_region:
            parts.append(f"regions-{config.region_count}")
        return "-".join(parts)

    def run_tests_for_file(
        self,
        file_path: Path,
        verbose: bool = True,
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Analyze a test case file and run appropriate YAML validation tests.

        Args:
            file_path: Path to test case file
            verbose: If True, print detailed output

        Returns:
            Tuple of (total_exit_code, list of failure info dicts)
        """
        analysis = self.analyze_file(file_path)
        configs = self.get_backend_configs(analysis)

        total_exit_code = 0
        failures = []

        for config in configs:
            exit_code, failure_info = self.run_yaml_test_for_config(
                config, file_path, verbose=verbose
            )
            total_exit_code += exit_code
            if failure_info:
                failures.append(failure_info)

        return total_exit_code, failures
