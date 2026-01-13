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

"""Data models for test case linting."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set


class Backend(str, Enum):
    """Supported test backends."""

    AWS = "aws"
    AZURE = "azure"
    GCE = "gce"
    DOCKER = "docker"
    BAREMETAL = "baremetal"
    K8S_LOCAL_KIND = "k8s-local-kind"
    K8S_GKE = "k8s-gke"
    K8S_EKS = "k8s-eks"
    XCLOUD = "xcloud"


@dataclass
class BackendConfig:
    """Configuration for a specific backend test run."""

    backend: Backend
    env_vars: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    multi_region: bool = False
    region_count: Optional[int] = None


@dataclass
class TestCaseAnalysis:
    """Analysis result for a test case file."""

    file_path: Path
    backends: Set[Backend]
    dc_count: Optional[int] = None
    explicit_backend: Optional[Backend] = None
    reason: str = ""
