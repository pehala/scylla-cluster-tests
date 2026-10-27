# Mini-Plan: Split SCTConfiguration.__init__ into load, validate and resolve

**Date:** 2026-10-22
**Estimated LOC:** ~700 moved, ~150 new (one PR, three commits)
**Related PR:** none yet

## Problem

`sdcm/sct_config/config.py:SCTConfiguration.__init__` is 580 lines doing three different jobs in
one body, so a rule cannot be tested without a full load, and loading cannot be reused without
the cloud lookups. The user's three claims about it, checked against the code:

| Claim | Verdict | Evidence |
|-------|---------|----------|
| It has two phases, load and validate | Partly. It has three. | Load is ~70 lines (defaults, backend yaml, user yaml, env, sizing). Validation is ~110 lines (auth, alternator, vector store, fullscan, dns names, network config, Azure NICs, k8s SNI, zero-token nodes, throttle steps, loader arch, minicloud endpoint). The remaining ~400 lines **resolve** values: billing project, resolved placement, loader image arch, AMI names, images for `scylla_version` on five backends, unified package, oracle and vector-store images, upgrade repo, repo symlinks, `user_prefix`, provision policy, snitch forcing, AWS capacity reservation, dedicated hosts, random driver version. |
| Validation should be model validators | Feasible, with one constraint. | `unit_tests/unit/config/test_mixin_validators.py` already proves mixin validators run on the assembled model. Verified on pydantic 2.13.5: `validate_assignment=True` re-runs every `mode="after"` model validator on each later `config[key] = value`, and a validator that assigns a field recurses forever. So rules must be pure checks, and they will also fire on runtime assignments (88 `params[...] = ...` sites in `sdcm/`). Today none of the `__init__` checks re-run after construction. |
| Load should be a separate class function | Feasible. | Nothing passes keyword arguments; all 30 production and 27 test call sites use bare `SCTConfiguration()`. `unit_tests/lib/fake_tester.py:FakeSCTConfiguration` overrides the env reader as an instance method and must follow it to a classmethod. |

Found on the way, not addressed by this plan: the `regions_data` branch calls `keys()` and `del` on
the model, neither of which exists, so it has always crashed when reached (no yaml sets it);
`_validate_perf_gradual_throttle_steps` runs in both `__init__` and `verify_configuration()`; the
local `region_names` captured before resolved placement is applied is stale for the image lookups
that follow it.

## Approach

Flow after the change, once: `SCTConfiguration.load()` merges every source into one mapping ->
builds the model from it with the plain pydantic constructor, so field and model validators see
the complete configuration -> runs the resolve steps in today's order -> returns the instance.
`init_and_verify_sct_config()` becomes `load()` + `verify_configuration()`, which stays as it is.

- **Load** becomes the classmethod `load()`; `__init__` is deleted, so `SCTConfiguration(**values)`
  is the plain pydantic constructor: validate the given values, run the rules, no I/O. `load()`
  merges the sources into one mapping with today's order and precedence (docker stress-image
  defaults, `defaults/test_default.yaml`, backend defaults, user config files, SCT_* environment),
  resolves constraint-based instance sizes on the mapping as the env path does today, builds the
  model, records provenance (which keys the user set, the sizing-resolved arch) and runs the
  resolve steps. No defaults are seeded into the mapping (verified: validating every field
  default explicitly fails on 303 `None` defaults; every `++`-appendable option defaults to `None`
  or `[]`, so append semantics hold on a plain dict).
- **Call sites**: all 57 bare `SCTConfiguration()` become `SCTConfiguration.load()`, mechanical.
  A bare `SCTConfiguration()` stays legal and yields a validated defaults-only model, which is
  what rule tests and `model_construct()`-style cheap builds want; a missed production caller
  fails fast on the missing `cluster_backend` and required params.
- **Validate** moves each pure check into a `@model_validator(mode="after")` on the mixin that
  owns the options, or on `SCTConfiguration` when the rule needs its helpers (`region_names`,
  network rules, instance catalog): auth credentials and snitch (scylla), alternator auth,
  vector-store credentials, k8s SNI/TLS, minicloud Azure endpoint, and on the model: AWS regions
  supported, `use_dns_names`, network config, Azure NICs, zero-token node counts, throttle steps,
  loader arch vs stress tools. `stress_duration`/`prepare_stress_duration` sign and `run_fullscan`
  JSON become field validators. Rules raise `ValueError`; pydantic reports them as
  `ValidationError`, a `ValueError` subclass, so `pytest.raises(ValueError, match=...)` holds.
  The two `assert` checks become `ValueError` too.
- **Rules are always on.** They also run on every later assignment. That is the pydantic contract
  and is treated as the intent here, not worked around with a validation context or a flag.
  Consequences, each verified before the PR: the resolve steps assign ~30 options after
  construction, so rules run on partially resolved state (every assigned value is itself valid,
  rules read other options); `sdcm/cluster_cloud.py` updates user and password one key at a time
  and only replaces non-empty defaults; a test that changes `stress_cmd` at runtime on an Arm
  loader now fails at that assignment instead of on the loader.
- **Resolve** runs inside `load()` after the model is built, in today's order, split into one
  named method per step so `load()` reads as the sequence above. Three checks stay here because they depend on resolved
  values: `instance_provision` after the duration policy, Docker simulated racks after the image
  tag is resolved, and `new_version` on AWS after the AMI is known. The snitch *forcing* stays
  here; only its check moves.
- Comments and docstrings that cite `__init__` step numbers are updated; the class docstring's
  "still to come" list shrinks accordingly.

Decided: `SCTConfiguration.load()` is the entry; the constructor is pure. Loading in `__init__`
hid file, env and cloud I/O behind a constructor and made every rule test need an environment.

Decisions still needed before coding:

1. Always-on rules as above (recommended), or keep today's load-only semantics. The latter needs
   a way to tell construction from assignment; pydantic offers only the validation context or
   `info.field_name`, both rejected as hacks in review.
2. Whether to delete the unreachable `regions_data` branch in the same PR or leave it.

## Files to Modify

- `sdcm/sct_config/config.py` -- `load()` classmethod (merge sources, build, provenance, ordered
  resolve calls), env reader and sizing resolution as classmethods over the mapping, `__init__`
  removed, resolve steps extracted into named methods, model-level validators for the
  helper-dependent rules, `init_and_verify_sct_config()` on top of `load()`.
- `sct.py`, `sct_ssh.py`, `sct_scan_issues.py`, `sdcm/utils/lint/validator.py`,
  `unit_tests/conftest.py` and the 26 other test modules calling `SCTConfiguration()` --
  `SCTConfiguration.load()`.
- `sdcm/sct_config/mixins/scylla.py`, `alternator.py`, `vector_store.py`, `stress.py`,
  `kubernetes.py`, `minicloud.py` -- validators for the rules on their own options.
- `sdcm/sct_config/helpers.py` -- import target for the shared `simulated_racks_enabled` rule
  (already there; no cycle, helpers imports only `types`).
- `unit_tests/lib/fake_tester.py` -- `FakeSCTConfiguration` env override becomes a classmethod.
- `unit_tests/unit/test_instance_sizing_config.py` -- direct sizing call uses the mapping form.
- `unit_tests/unit/config/test_init_split.py` (new) -- `load()` merges sources with provenance
  and runs the resolve steps; each moved rule rejects and accepts through the plain constructor,
  no env or yaml; a rule also fires on assignment; `model_construct()` still bypasses all rules.

## Verification

- [ ] Baseline before the change: 1517 passed in `unit_tests/unit/test_config.py`,
      `unit_tests/unit/config/`, `test_sct_config_validators.py`, `test_duration_provision_policy.py`,
      `test_perf_gradual_config.py`, `test_instance_sizing_config.py`, `test_tester.py`,
      `test_gce_use_dns_names.py`; same count or more after.
- [ ] `uv run pytest unit_tests/unit/test_lint_patch_targets.py` passes: every
      `sdcm.sct_config.config.<name>` the pipeline linter patches is still bound there.
- [ ] `uv run sct.py lint-pipelines` on one AWS and one Docker jenkinsfile gives the same result
      as on master.
- [ ] `grep -rn "SCTConfiguration()" sdcm sct*.py` finds no production caller;
      `FakeSCTConfiguration.load()` still loads the docker PR test case in
      `unit_tests/unit/test_tester.py`.
- [ ] `SCTConfiguration(authenticator="PasswordAuthenticator")` raises without any env or yaml.
- [ ] Time `SCTConfiguration()` for the docker minimal config before and after; the always-on
      rules that read `region_names` re-parse the environment on each assignment, so the budget
      is +10% or the rules read the option directly.
- [ ] `uv run sct.py pre-commit` passes.
