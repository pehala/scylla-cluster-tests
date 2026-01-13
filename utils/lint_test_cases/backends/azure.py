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

"""Azure backend implementation for test case linting."""

from typing import List

from utils.lint_test_cases.models import Backend, BackendConfig, TestCaseAnalysis
from . import BaseBackend


class AzureBackend(BaseBackend):
    """Azure backend implementation."""

    @property
    def backend_type(self) -> Backend:
        return Backend.AZURE

    @property
    def content_keys(self) -> List[str]:
        return ["azure_region_name", "azure_instance_type_db", "azure_image_db", "azure_image_monitor"]

    def get_configs(self, analysis: TestCaseAnalysis) -> List[BackendConfig]:
        """Generate Azure backend configuration."""
        return [
            BackendConfig(
                backend=Backend.AZURE,
                env_vars={
                    "SCT_AZURE_IMAGE_DB": "image",
                    "SCT_AZURE_REGION_NAME": "eastus",
                },
                description="Azure",
            )
        ]
