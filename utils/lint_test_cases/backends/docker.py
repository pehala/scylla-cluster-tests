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

"""Docker backend implementation for test case linting."""

import re
from typing import List, Pattern

from utils.lint_test_cases.models import Backend, BackendConfig, TestCaseAnalysis
from . import BaseBackend


class DockerBackend(BaseBackend):
    """Docker backend implementation."""

    # Pre-compiled regex patterns for filename matching
    _FILENAME_PATTERNS: List[Pattern[str]] = [
        re.compile(r"docker", re.IGNORECASE)
    ]

    @property
    def backend_type(self) -> Backend:
        return Backend.DOCKER

    @property
    def filename_patterns(self) -> List[Pattern[str]]:
        return self._FILENAME_PATTERNS

    @property
    def content_keys(self) -> List[str]:
        return ["docker_image", "docker_network"]

    def get_configs(self, analysis: TestCaseAnalysis) -> List[BackendConfig]:
        """Generate Docker backend configuration."""
        return [
            BackendConfig(
                backend=Backend.DOCKER,
                env_vars={
                    "SCT_DOCKER_IMAGE": "scylladb/scylla",
                    "SCT_USE_MGMT": "false",
                },
                description="Docker",
            )
        ]
