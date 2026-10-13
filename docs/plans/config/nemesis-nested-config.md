---
status: in_progress
domain: config
created: 2026-10-09
last_updated: 2026-10-13
owner: pehala
---

# Nested Nemesis Configuration with Per-Runner Parameters

## 1. Problem Statement

Nemesis behaviour is configured through 11 flat top-level options with a `nemesis_` prefix
(`nemesis_class_name`, `nemesis_selector`, `nemesis_seed`, `nemesis_interval`, ...). This causes:

- **Parallel lists instead of structure.** Running several nemesis threads (runners) requires
  `nemesis_class_name`, `nemesis_selector` and `nemesis_seed` to be index-aligned lists. The
  pairing is implicit and only checked by a dedicated length-parity validator. 14 test-case /
  configuration files use multi-runner setups today.
- **No per-runner parameters beyond selector and seed.** `nemesis_interval`,
  `nemesis_multiply_factor` and `nemesis_filter_seeds` are global. A test cannot run e.g. a fast
  non-disruptive runner next to a slow disruptive one. Each new per-runner parameter under the
  current scheme means another parallel list plus another parity check.
- **Runner-specific options only from Python.** `CategoricalMonkey` needs a weight distribution,
  which can only be passed to its constructor, so `cdc_replication_test.py` builds that runner by
  hand instead of from the test-case YAML.
- **Two ways into a runner.** Runners read some options from constructor kwargs and others
  straight from `params`, with precedence rules between them.
- **Mixed concerns in one namespace.** Runner settings, test-flow settings
  (`nemesis_during_prepare`) and disruption-specific knobs (`nemesis_add_node_cnt`,
  `nemesis_double_load_during_grow_shrink_duration`, `nemesis_sequence_sleep_between_ops`) sit
  side by side with nothing showing which applies where.

## 2. Current State

State on `master`, before Phase 1.

### Config definition

- `sdcm/sct_config/mixins/nemesis.py:NemesisConfigMixin` — defines all 11 flat `nemesis_*` fields
  (plus unrelated `sla`).
- `defaults/test_default.yaml` — defaults for `nemesis_class_name` (`NoOpMonkey`),
  `nemesis_during_prepare`, `nemesis_interval`, `nemesis_add_node_cnt`, `nemesis_filter_seeds`,
  `nemesis_multiply_factor`, `nemesis_double_load_during_grow_shrink_duration`.
- `sdcm/sct_config/config.py:SCTConfiguration`:
  - `_validate_nemesis_parallel_config` — selector/seed list length must be 1 or equal to the
    number of runners.
  - `_validate_value` — special case for `nemesis_selector` when several runners exist.
  - filter-seeds vs. seed-count check and the backend check for
    `nemesis_grow_shrink_instance_type`.
  - `get` — dotted keys (`stress_image.ycsb`) traverse only `dict` values.
- `sdcm/sct_config/helpers.py:merge_dicts_append_strings` — merges sources with
  `anyconfig.MS_DICTS`: dicts deep-merge, lists are replaced wholesale. A value that is already a
  pydantic model is replaced wholesale, not deep-merged.
- `sdcm.nemesis` imports `sdcm.sct_config` at module level (through `sdcm.cluster` and provisioning
  modules), so the config cannot import the runner classes.

### Runtime consumers

| Option | Consumers |
|---|---|
| `nemesis_class_name`, `nemesis_selector`, `nemesis_seed` | `sdcm/tester.py:ClusterTester.get_nemesis_class` builds per-thread dicts; `sdcm/cluster.py:BaseScyllaCluster.add_nemesis` and `sdcm/cluster_cassandra.py:BaseCassandraCluster.add_nemesis` pass selector/seed as constructor kwargs; `grow_cluster_test.py` |
| `nemesis_selector` | also `NemesisRunner.nemesis_selector`, which falls back to the flat option when no selector was passed |
| `nemesis_seed` | also `sdcm/utils/operations_thread.py` (takes first element) |
| `nemesis_interval` | `sdcm/nemesis/__init__.py:NemesisRunner`, `performance_regression_test.py`, `ycsb_performance_regression_test.py` |
| `nemesis_multiply_factor` | `NemesisRunner.shuffle_list_of_disruptions` |
| `nemesis_filter_seeds` | `NemesisRunner`, config validation |
| `nemesis_during_prepare` | `longevity_test.py`, `longevity_lwt_test.py`, `longevity_twcs_test.py`, `longevity_alternator_ttl_test.py`, `sdcm/utils/loader_utils.py` |
| `nemesis_add_node_cnt`, `nemesis_grow_shrink_instance_type` | `sdcm/nemesis/utils/topology_ops.py`, `sdcm/nemesis/monkey/grow_shrink.py`, `longevity_balancer_test.py`, `sdcm/provision/aws/capacity_reservation.py`; instance type also in `sdcm/provision/aws/az_resolver.py`, `sdcm/provision/gce/zone_resolver.py` |
| `nemesis_double_load_during_grow_shrink_duration`, `nemesis_sequence_sleep_between_ops` | `sdcm/nemesis/monkey/grow_shrink.py`, a sequence disruption in `NemesisRunner` |

### Usage footprint

| Option | YAML files (`test-cases/`, `configurations/`, `defaults/`) |
|---|---|
| `nemesis_class_name` | 309 |
| `nemesis_selector` | 216 |
| `nemesis_seed`, `nemesis_interval` | 79 each |
| `nemesis_during_prepare` | 69 |
| others | 1–16 each |

- No Jenkins pipeline or `vars/` Groovy file references these options.
- 14 overlay files set `nemesis_selector`/`seed`/`interval`/`during_prepare` without
  `nemesis_class_name`.
- `templates/test_config/template-nemesis-config.yaml.j2` (used by `sct.py` nemesis YAML /
  pipeline generation) emits `nemesis_class_name` and `nemesis_selector`.
- Docs/skills mentioning the keys: `docs/nemesis.md`, `docs/configuration_options/`, `AGENTS.md`,
  `README.md`, `skills/writing-nemesis`, `skills/downscaling-for-minicloud`,
  `skills/labeling-pipelines`.

## 3. Goals

1. Runners and their options are declared under one `nemesis:` key; every runner, single-runner
   tests included, is an entry of `nemesis.runners`.
2. Each runner can set `selector`, `seed`, `interval`, `multiply_factor`, `filter_seeds`; unset
   values come from the `nemesis:` defaults.
3. Each runner class defines which options its entry accepts; an entry is validated against its
   runner class at config load (unknown class, unknown option, missing required option, out-of-range
   value all fail before the test starts).
4. A runner receives its resolved config as a required constructor argument and reads every
   option from it; no runner reads nemesis options from `params`.
5. Parallel-list parity validation is deleted; runner/parameter pairing is structural.
6. After Phase 3, no flat `nemesis_*` option remains.
7. Generated config docs describe the nested option and its sub-options.

### Non-goals

- Keeping flat runner keys working alongside the nested form. Repo YAMLs are migrated in one step
  (Phase 3) instead of being translated at load time.
- `sla` is not a nemesis option; untouched.
- Per-disruption parameter overrides per runner (e.g. different `add_node_cnt` per runner).

## 4. Implementation Phases

### Target shape

```yaml
nemesis:
  # Defaults for every runner
  interval: 5
  seed: 123
  multiply_factor: 2
  filter_seeds: false
  selector: "not disruptive"
  runners:
    - SisyphusMonkey: {}
    - SisyphusMonkey:
        selector: "disruptive"
        interval: 15
        seed: 456
    - CategoricalMonkey:
        dist: {StopStartMonkey: 2, HardRebootNodeMonkey: 1}
        default_weight: 0
```

- Each `runners` item is a single-key mapping `{<RunnerClass>: {<options>}}`.
- Overlays: the `nemesis:` defaults deep-merge across config sources; `runners` is a list, so a
  source that sets it replaces the whole list.
- Env vars: `SCT_NEMESIS__INTERVAL=10`; `SCT_NEMESIS__RUNNERS` takes a JSON/YAML string.
- A runner without a `seed` (own or default) gets a random one when the runners are resolved.

### Runner config models

- `NemesisRunnerConfig` (in `sdcm/nemesis/`) is the model every runner uses by default: the common
  options above, each "unset" by default. Unknown options are rejected.
- A runner with options of its own defines a subclass next to the runner and points its
  `config_model` at it — today only `CategoricalMonkey` (`CategoricalMonkeyConfig`: required
  `dist`, `default_weight`).
- The `nemesis` option model is built from the runner registry (`NemesisRegistry` over
  `NemesisRunner`): every runner class becomes one member of a discriminated union, tagged by its
  class name and validated by its `config_model`. A new runner needs no config change.
- Each validated entry knows the runner class it names, so the tester never looks a class up by
  name.
- `NemesisDefaults.resolve` fills a runner's unset options from the `nemesis:` defaults without
  changing the stored runners, so a later config source changing a default still reaches every
  runner. `nemesis_threads()` returns one `(runner class, resolved config)` pair per runner.

Phases 1–3 ship in one PR as separate commits: until Phase 3 rewrites the YAMLs, test cases that
set only flat keys run the default `NoOpMonkey` and lose their flat nemesis settings.

### Phase 1 — Nested runner config consumed by runners (Importance: Critical) — done

- Add the `nemesis` option and the runner config models above; `defaults/test_default.yaml`
  declares a single `NoOpMonkey` runner.
- Break the `sdcm.nemesis` → `sdcm.sct_config` import cycle so the config can build its model from
  the runner classes (backend helpers move to `sdcm/utils/cloud_backends.py`; modules that only
  annotated `SCTConfiguration` import it for type checking only).
- `SCTConfiguration.get` traverses model attributes (`get("nemesis.interval")`); a config source
  deep-merges into a model-typed option set by an earlier source instead of replacing it.
- `NemesisRunner` and `CategoricalMonkey` take the resolved config as a required constructor
  argument; the selector/seed/dist kwargs and the flat-option fallbacks are removed.
- `get_nemesis_class` returns `nemesis_threads()`; `add_nemesis` constructs each runner from its
  pair. The flat runner keys are no longer read when starting runners.
- Nemesis checks in `SCTConfiguration` other than the grow/shrink instance-type one are removed:
  the selector/seed parity check and the `nemesis_selector` special case in `_validate_value` have
  nothing to check with nested runners; the filter-seeds vs. seed-count check is dropped because
  the node allocator already fails a disruption with "node allocation failed" when no non-seed
  node is available.
- `cdc-replication-longevity.yaml` declares its `CategoricalMonkey` distribution, keyed by nemesis
  class names (the method-style keys it used in Python never matched any disruption);
  `cdc_replication_test.py` starts it through `get_nemesis_class`.
- A runner config naming disruptions (CategoricalMonkey `dist`) is checked against the registered
  nemesis classes at config load.
- The `nemesis` option accepts YAML or JSON from `SCT_NEMESIS` as well as from `SCT_NEMESIS__<sub-key>`.
- Generated config docs list the sub-options of model-typed options, nested models as dotted names.

**DoD:** runners start only from `nemesis.runners`; a two-runner config with different intervals
gives each runner its own interval; invalid entries fail at config load with the runner index and
class in the error location.

### Phase 2 — Nest the remaining nemesis options (Importance: Medium) — done

- `nemesis_during_prepare` → `nemesis.during_prepare`; `nemesis_sequence_sleep_between_ops` →
  `nemesis.sequence_sleep_between_ops`; grow/shrink knobs → `nemesis.grow_shrink`
  (`add_node_cnt`, `instance_type`, `double_load_duration`). Defaults live on the model.
- The flat options stay in the model until Phase 3, described as replaced and no longer read.
- `SCTConfiguration.get` returns falsy nested values (`false`, `0`) instead of `None`.
- The AWS AZ resolver, GCE zone resolver and capacity reservation list the instance type by its
  dotted key (`nemesis.grow_shrink.instance_type`), so it is still checked for AZ/zone availability
  and reserved.
- Readers listed in Current State switch to the nested values, as do the remaining readers of
  runner options outside a runner: performance tests (`interval`; they no longer pass it to
  `start_nemesis`, so each runner keeps its own), `operations_thread.py` (`seed`),
  `grow_cluster_test.py` (runner classes).
- The grow/shrink instance-type check, the only nemesis check left in `SCTConfiguration` (it needs
  backend, regions and cloud API calls), reads the nested value.

**DoD:** no code reads a flat `nemesis_*` option.

### Phase 3 — Migrate repo YAMLs and remove flat options (Importance: Critical)

Runs once every option has its nested form, so each YAML is rewritten in a single pass.

- Scripted rewrite of `test-cases/`, `configurations/` and `defaults/` from every flat
  `nemesis_*` key to `nemesis:`, preserving comments
  and key order. Parallel lists become one runner entry each. Commit the script.
- Overlay rule: config sources deep-merge `nemesis:` but replace the `runners` list whole, so an
  overlay cannot change one option of one runner. Overlays that only tune selector/seed/interval
  (the 14 found today) become `nemesis:` defaults, which reach only runner entries that leave that
  option unset; the migration therefore writes those options as `nemesis:` defaults in the base
  test case too, not on its runner entries, unless the runners differ. An overlay that must change
  a runner-specific option restates the whole `runners` list.
- Update `templates/test_config/template-nemesis-config.yaml.j2` and `sct.py` nemesis YAML /
  pipeline generation.
- Remove the flat fields from `NemesisConfigMixin`; a flat key then fails at load as an unknown
  option.

**DoD:** no flat `nemesis_*` key in repo YAMLs or in the config model; a script loading every repo YAML on the parent commit and on the branch
reports the same runners, selectors, seeds, intervals and nested values.

### Phase 4 — Documentation and skills (Importance: Medium)

- Regenerate `docs/configuration_options*`; update `docs/nemesis.md`, `AGENTS.md`, `README.md`,
  `.github/copilot-instructions.md`, and the `writing-nemesis`, `downscaling-for-minicloud`,
  `labeling-pipelines`, `migrate-to-sizing` skills.
- Document per-runner overrides and runner-specific options with a two-runner example, and how a
  runner adds its own config model.

**DoD:** `grep -rn "nemesis_class_name\|nemesis_selector" docs skills AGENTS.md README.md` returns
only migration notes.

## 5. Testing Requirements

- **Unit (Phase 1, done):**
  - `unit_tests/unit/nemesis/test_runner_config.py` — entry validation by runner class (model
    selection, missing / foreign / out-of-range option, unknown class, several classes in one
    entry) and default resolution, using a test-only runner hierarchy instead of real runners.
  - `unit_tests/unit/config/test_nemesis_runners.py` — loading from a config file, overlay
    deep-merge, env var override, import-cycle guard.
  - `unit_tests/unit/nemesis/monkey/test_sisyphus.py`, `test_categorical_monkey.py` — runners read
    their options from the config they are given.
- **Unit (Phase 2):** grow/shrink instance-type check with the nested value; readers use
  the nested values; AZ/zone resolvers and capacity reservation include
  `nemesis.grow_shrink.instance_type`.
- **Unit (Phase 3):** migration script on representative single-runner, parallel-runner and
  overlay files.
- **Equivalence script (Phase 3):** load every YAML in `test-cases/` and `configurations/` on
  the parent commit and on the branch; compare resolved runners and nested values.
- **Manual / CI:** artifact test, one single-runner longevity, one parallel-nemesis longevity,
  `cdc-replication-longevity` (CategoricalMonkey from YAML),
  `perf-regression-latency-backup-nemesis` (reads `interval` outside a runner), one GrowShrink
  test (`add_node_cnt`, capacity reservation). Provision labels: `provision-aws`.

## 6. Success Criteria

- All phase DoD items met.
- Equivalence script reports zero differences across all repo YAMLs.
- A test case can declare two runners with different `interval` values, and a `CategoricalMonkey`
  distribution, in YAML alone.

## 7. Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Phase 1 or 2 merged without Phase 3: flat-only test cases silently run `NoOpMonkey` | Medium | High | Ship Phases 1–3 in one PR; equivalence script in CI for the PR |
| Overlay setting `runners` silently replaces the whole list | Medium | Medium | Defaults live outside `runners`, so overlays that only tune runners set defaults; migration script keeps known overlays default-only |
| Backported test-case edits written in nested form land on branches that only know flat keys | High | Medium | **Needs Investigation:** which branches still receive test-case backports; backport Phases 1–3 there or hand-translate backported YAML edits |
| Out-of-tree / personal configs use flat keys | Medium | Low | Removed flat fields fail at load as unknown options, naming the key; migration notes in docs |
| `sdcm.sct_config` now imports `sdcm.nemesis`, raising config import time (≈3.4 s → ≈3.8 s measured) | High | Low | Import-cycle guard test; revisit with lazy imports (PEP 810) |
| AZ/zone resolvers or capacity reservation miss the nested grow/shrink instance type, so a GrowShrink nemesis hits a capacity error mid-test | Low | High | Unit tests for both resolvers and the reservation with the nested key set |
| Runner class names used as config keys: renaming a runner breaks YAMLs | Low | Medium | Unknown class fails at load and lists valid names |
| External tools read flat keys from run params (Argus UI, dashboards) | Low | Medium | **Needs Investigation:** check Argus for `nemesis_class_name`/`nemesis_selector` consumers before Phase 3 removes flat fields |
| Conflict with "Typed Config Access Migration" (#13878) | Medium | Low | Coordinate access idiom (`params.get("nemesis.x")` vs typed attribute) with that PR |

## Related Plans

- [nemesis-rework.md](../nemesis/nemesis-rework.md) — runner/disruption split this builds on.
- [config-type-normalization.md](config-type-normalization.md) — normalized `nemesis_seed` list
  handling; this plan removes the list form.
- Typed Config Access Migration (#13878).
