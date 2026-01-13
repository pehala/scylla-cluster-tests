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

"""AWS backend implementation for test case linting."""

from typing import List

from sdcm.sct_config import SCTConfiguration

from utils.lint_test_cases.models import Backend, BackendConfig, TestCaseAnalysis
from . import BaseBackend


class AWSBackend(BaseBackend):
    """AWS backend implementation."""

    @property
    def backend_type(self) -> Backend:
        return Backend.AWS

    @property
    def content_keys(self) -> List[str]:
        return ["region_name", "instance_type_db", "ami_id_db_scylla"]

    def get_configs(self, analysis: TestCaseAnalysis) -> List[BackendConfig]:
        """Generate AWS backend configurations."""
        configs = []

        if analysis.dc_count > 1:
            # Multi DC configuration
            configs.append(
                BackendConfig(
                    backend=Backend.AWS,
                    env_vars={
                        "SCT_AMI_ID_DB_SCYLLA": " ".join(f"ami-{i}" for i in range(analysis.dc_count)),
                        "SCT_REGION_NAME": " ".join(SCTConfiguration.aws_supported_regions[: analysis.dc_count]),
                        "SCT_SCYLLA_REPO": "http://downloads.scylladb.com.s3.amazonaws.com/rpm/centos/scylla-2025.1.repo",
                    },
                    description=f"AWS multi-DC with {analysis.dc_count} regions",
                    multi_region=True,
                    region_count=analysis.dc_count,
                )
            )
        else:
            # Single DC AWS
            configs.append(
                BackendConfig(
                    backend=Backend.AWS,
                    env_vars={
                        "SCT_AMI_ID_DB_SCYLLA": "ami-1234",
                        "SCT_SCYLLA_REPO": "http://downloads.scylladb.com.s3.amazonaws.com/rpm/centos/scylla-2025.1.repo",
                    },
                    description="AWS single region",
                )
            )

        return configs
