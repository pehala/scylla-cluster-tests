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

"""
Module to assess test case configuration files and determine which backend(s) should be used.

This module analyzes YAML test case files to determine the appropriate backend(s) for linting
based on filename patterns, content, and configuration values.
"""

from utils.lint_test_cases.models import Backend, BackendConfig, TestCaseAnalysis
from utils.lint_test_cases.analyzer import TestCaseAnalyzer
from utils.lint_test_cases.cli import main

__all__ = [
    "Backend",
    "BackendConfig",
    "TestCaseAnalysis",
    "TestCaseAnalyzer",
    "main",
]
