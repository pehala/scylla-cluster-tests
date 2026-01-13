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

"""Baremetal backend implementation for test case linting."""

from typing import List

from utils.lint_test_cases.models import Backend, BackendConfig, TestCaseAnalysis
from . import BaseBackend


class BaremetalBackend(BaseBackend):
    """Baremetal backend implementation."""

    @property
    def backend_type(self) -> Backend:
        return Backend.BAREMETAL

    @property
    def content_keys(self) -> List[str]:
        return ["db_nodes_public_ip", "db_nodes_private_ip", "s3_baremetal_config"]

    def get_configs(self, analysis: TestCaseAnalysis) -> List[BackendConfig]:
        """Generate Baremetal backend configuration."""
        return [
            BackendConfig(
                backend=Backend.BAREMETAL,
                env_vars={
                    "SCT_DB_NODES_PUBLIC_IP": '["127.0.0.1", "127.0.0.2"]',
                    "SCT_SCYLLA_REPO": "http://downloads.scylladb.com.s3.amazonaws.com/rpm/centos/scylla-2025.1.repo",
                },
                description="Baremetal",
            )
        ]
