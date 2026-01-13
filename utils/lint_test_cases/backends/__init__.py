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

"""Backend implementations for test case linting.

This module exposes the concrete backend handlers and provides the
`BaseBackend` abstract class so that other modules can import a
single symbol from `utils.lint_test_cases.backends`.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Pattern

from utils.lint_test_cases.models import Backend, BackendConfig, TestCaseAnalysis


class BaseBackend(ABC):
    """Abstract base class for backend implementations."""

    @property
    @abstractmethod
    def backend_type(self) -> Backend:
        """Return the backend type enum value."""

    @property
    def filename_patterns(self) -> List[Pattern[str]]:
        """Return compiled regex patterns to match in filenames for this backend."""
        return []

    @property
    def content_keys(self) -> List[str]:
        """Return YAML keys that indicate this backend."""
        return []

    def matches_filename(self, filepath: str) -> bool:
        """Check if the filepath matches any filename patterns for this backend."""
        return any(pattern.search(filepath.lower()) for pattern in self.filename_patterns)

    def matches_content(self, content: Optional[Dict[str, Any]]) -> bool:
        """Check if the YAML content contains keys for this backend."""
        return bool(content) and any(key in content for key in self.content_keys)

    @abstractmethod
    def get_configs(self, analysis: TestCaseAnalysis) -> List[BackendConfig]:
        """Generate backend configurations for linting."""


class SimpleBackend(BaseBackend):
    """Simple backend with declarative configuration."""

    def __init__(self, backend: Backend, keys: List[str], env_vars: Dict[str, str], description: str):
        self._backend, self._keys, self._env_vars, self._description = backend, keys, env_vars, description

    @property
    def backend_type(self) -> Backend:
        return self._backend

    @property
    def content_keys(self) -> List[str]:
        return self._keys

    def get_configs(self, analysis: TestCaseAnalysis) -> List[BackendConfig]:
        return [BackendConfig(backend=self._backend, env_vars=self._env_vars, description=self._description)]

# Simple backends


def AzureBackend() -> SimpleBackend:  # noqa: N802
    """Create Azure backend."""
    return SimpleBackend(
        backend=Backend.AZURE,
        keys=["azure_region_name", "azure_instance_type_db", "azure_image_db", "azure_image_monitor"],
        env_vars={"SCT_AZURE_IMAGE_DB": "image", "SCT_AZURE_REGION_NAME": "eastus"},
        description="Azure",
    )


def BaremetalBackend() -> SimpleBackend:  # noqa: N802
    """Create Baremetal backend."""
    return SimpleBackend(
        backend=Backend.BAREMETAL,
        keys=["db_nodes_public_ip", "db_nodes_private_ip", "s3_baremetal_config"],
        env_vars={
            "SCT_DB_NODES_PUBLIC_IP": '["127.0.0.1", "127.0.0.2"]',
            "SCT_SCYLLA_REPO": "http://downloads.scylladb.com.s3.amazonaws.com/rpm/centos/scylla-2025.1.repo",
        },
        description="Baremetal",
    )
