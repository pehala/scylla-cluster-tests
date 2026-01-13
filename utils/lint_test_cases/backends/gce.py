# Copyright (c) 2025 ScyllaDB

from typing import Any, List
from utils.lint_test_cases.models import Backend, BackendConfig, TestCaseAnalysis
from . import BaseBackend


class GCEBackend(BaseBackend):
    """GCE (Google Cloud) backend implementation."""

    @property
    def backend_type(self) -> Backend:
        return Backend.GCE

    @property
    def content_keys(self) -> List[str]:
        return ["gce_datacenter", "gce_instance_type_db", "gce_image_db"]

    def matches_content(self, content: dict[str, Any] | None) -> bool:
        """Check if the YAML content contains keys for this backend."""
        return bool(content and (any(k in content for k in self.content_keys) or
                                 content.get("endpoint_snitch") == "GoogleCloudSnitch"))

    def get_configs(self, analysis: TestCaseAnalysis) -> List[BackendConfig]:
        """Generate GCE backend configurations."""
        base_env = {
            "SCT_GCE_IMAGE_DB": "image",
            "SCT_SCYLLA_REPO": "http://downloads.scylladb.com.s3.amazonaws.com/rpm/centos/scylla-2025.1.repo",
        }

        if analysis.dc_count > 1:
            return [BackendConfig(
                backend=Backend.GCE,
                env_vars={**base_env,
                    "SCT_GCE_DATACENTER": " ".join(["us-east1", "us-west1", "eu-north1"][:analysis.dc_count]),
                          },
                description=f"GCE multi-DC with {analysis.dc_count} regions",
                multi_region=True,
                region_count=analysis.dc_count,
            )]

        return [BackendConfig(backend=Backend.GCE, env_vars=base_env, description="GCE single region")]
