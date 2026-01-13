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

"""Kubernetes backend implementations for test case linting."""

from typing import List

from sdcm.sct_config import SCTConfiguration

from utils.lint_test_cases.models import Backend, BackendConfig, TestCaseAnalysis
from . import BaseBackend


class K8sBaseBackend(BaseBackend):
    """Base class for Kubernetes backends."""

    @property
    def content_keys(self) -> List[str]:
        return [
            "k8s_n_scylla_pods_per_cluster",
            "k8s_scylla_operator_docker_image",
            "k8s_loader_run_type",
        ]


class K8sLocalKindBackend(K8sBaseBackend):
    """Kubernetes Local Kind backend implementation."""

    @property
    def backend_type(self) -> Backend:
        return Backend.K8S_LOCAL_KIND

    def get_configs(self, analysis: TestCaseAnalysis) -> List[BackendConfig]:
        """Generate K8S Local Kind backend configuration."""
        return [
            BackendConfig(
                backend=Backend.K8S_LOCAL_KIND,
                env_vars={
                    "SCT_AMI_ID_DB_SCYLLA": "ami-1234",
                },
                description="Kubernetes (k8s-local-kind)",
            )
        ]


class K8sEKSBackend(K8sBaseBackend):
    """Kubernetes EKS backend implementation."""

    @property
    def backend_type(self) -> Backend:
        return Backend.K8S_EKS

    @property
    def content_keys(self) -> List[str]:
        base_keys = super().content_keys
        return base_keys + ["k8s_minio_storage_size"]

    def get_configs(self, analysis: TestCaseAnalysis) -> List[BackendConfig]:
        """Generate K8S EKS backend configuration."""
        env_vars = {"SCT_AMI_ID_DB_SCYLLA": "ami-1234"}
        description = "Kubernetes EKS"

        if analysis.dc_count:
            env_vars["SCT_REGION_NAME"] = " ".join(
                SCTConfiguration.aws_supported_regions[: analysis.dc_count]
            )
            description = f"Kubernetes EKS multi-DC with {analysis.dc_count} regions"

        return [
            BackendConfig(
                backend=Backend.K8S_EKS,
                env_vars=env_vars,
                description=description,
            )
        ]


class K8sGKEBackend(K8sBaseBackend):
    """Kubernetes GKE backend implementation."""

    @property
    def backend_type(self) -> Backend:
        return Backend.K8S_GKE

    @property
    def content_keys(self) -> List[str]:
        base_keys = super().content_keys
        return base_keys + ["k8s_minio_storage_size"]

    def get_configs(self, analysis: TestCaseAnalysis) -> List[BackendConfig]:
        """Generate K8S GKE backend configuration."""
        env_vars = {"SCT_GCE_IMAGE_DB": "image"}
        description = "Kubernetes GKE"

        if analysis.dc_count:
            env_vars["SCT_GCE_DATACENTER"] = " ".join(
                ["us-east1", "us-west1", "eu-north1"][0: analysis.dc_count]
            )
            description = f"Kubernetes GKE multi-DC with {analysis.dc_count} regions"

        return [
            BackendConfig(
                backend=Backend.K8S_GKE,
                env_vars=env_vars,
                description=description,
            )
        ]
