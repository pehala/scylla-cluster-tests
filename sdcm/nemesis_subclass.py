import inspect
import time
import random
from typing import Tuple, List, Callable, Set, Dict

from sdcm.nemesis import Nemesis, NemesisBaseClass


class SisyphusMonkey(Nemesis):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disruptions_list = self.build_disruptions_by_selector(self.nemesis_selector)
        self.shuffle_list_of_disruptions(self.disruptions_list)

    def disrupt(self):
        self.call_next_nemesis()


class SslHotReloadingNemesis(NemesisBaseClass):
    disruptive = False
    config_changes = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_hot_reloading_internode_certificate()


class PauseLdapNemesis(NemesisBaseClass):
    disruptive = False
    limited = True

    def __init__(self, runner):
        runner.disrupt_ldap_connection_toggle()


class ToggleLdapConfiguration(NemesisBaseClass):
    disruptive = True
    limited = True

    def __init__(self, runner):
        runner.disrupt_disable_enable_ldap_authorization()


class NoOpMonkey(Nemesis):
    kubernetes = True

    def disrupt(self):
        time.sleep(300)


class AddRemoveDcNemesis(NemesisBaseClass):

    disruptive = True
    kubernetes = False
    run_with_gemini = False
    limited = True
    topology_changes = True

    def __init__(self, runner):
        runner.disrupt_add_remove_dc()


class GrowShrinkClusterNemesis(NemesisBaseClass):
    disruptive = True
    kubernetes = True
    topology_changes = True

    def __init__(self, runner):
        runner.disrupt_grow_shrink_cluster()


class AddRemoveRackNemesis(NemesisBaseClass):
    disruptive = True
    kubernetes = True
    config_changes = True

    def __init__(self, runner):
        runner.disrupt_grow_shrink_new_rack()


class StopWaitStartMonkey(NemesisBaseClass):
    disruptive = True
    supports_high_disk_utilization = True
    kubernetes = True
    limited = True
    zero_node_changes = True

    def __init__(self, runner):
        runner.disrupt_stop_wait_start_scylla_server(600)


class StopStartMonkey(NemesisBaseClass):
    disruptive = True
    supports_high_disk_utilization = True
    kubernetes = True
    limited = True

    def __init__(self, runner):
        runner.disrupt_stop_start_scylla_server()


class EnableDisableTableEncryptionAwsKmsProviderWithRotationMonkey(NemesisBaseClass):
    disruptive = True
    kubernetes = False  # Enable it when EKS SCT code starts supporting the KMS service

    def __init__(self, runner):
        runner.disrupt_enable_disable_table_encryption_aws_kms_provider_with_rotation()


class EnableDisableTableEncryptionAwsKmsProviderWithoutRotationMonkey(NemesisBaseClass):
    disruptive = True
    kubernetes = False  # Enable it when EKS SCT code starts supporting the KMS service

    def __init__(self, runner):
        runner.disrupt_enable_disable_table_encryption_aws_kms_provider_without_rotation()


class EnableDisableTableEncryptionAwsKmsProviderMonkey(Nemesis):
    disruptive = True
    kubernetes = False  # Enable it when EKS SCT code starts supporting the KMS service

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disruptions_list = self.build_disruptions_by_name([
            'disrupt_enable_disable_table_encryption_aws_kms_provider_without_rotation',
            'disrupt_enable_disable_table_encryption_aws_kms_provider_with_rotation',
        ])
        self.shuffle_list_of_disruptions(self.disruptions_list)

    def disrupt(self):
        self.call_next_nemesis()


class RestartThenRepairNodeMonkey(NemesisBaseClass):
    disruptive = True
    kubernetes = True

    def __init__(self, runner):
        runner.disrupt_restart_then_repair_node()


class MultipleHardRebootNodeMonkey(NemesisBaseClass):
    disruptive = True
    supports_high_disk_utilization = True
    kubernetes = True
    free_tier_set = True

    def __init__(self, runner):
        runner.disrupt_multiple_hard_reboot_node()


class HardRebootNodeMonkey(NemesisBaseClass):
    disruptive = True
    supports_high_disk_utilization = True
    kubernetes = True
    limited = True
    free_tier_set = True

    def __init__(self, runner):
        runner.disrupt_hard_reboot_node()


class SoftRebootNodeMonkey(NemesisBaseClass):
    disruptive = True
    supports_high_disk_utilization = True
    kubernetes = True
    limited = True
    free_tier_set = True

    def __init__(self, runner):
        runner.disrupt_soft_reboot_node()


class DrainerMonkey(NemesisBaseClass):
    disruptive = True
    kubernetes = True
    limited = True
    topology_changes = True

    def __init__(self, runner):
        runner.disrupt_nodetool_drain()


class CorruptThenRepairMonkey(NemesisBaseClass):
    disruptive = True
    kubernetes = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_destroy_data_then_repair()


class CorruptThenRebuildMonkey(NemesisBaseClass):
    disruptive = True
    kubernetes = True

    def __init__(self, runner):
        runner.disrupt_destroy_data_then_rebuild()


class DecommissionMonkey(NemesisBaseClass):
    disruptive = True
    limited = True
    topology_changes = True
    supports_high_disk_utilization = False  # Decommissioning a node cause increase of disk space across rest of the nodes

    def __init__(self, runner):
        runner.disrupt_nodetool_decommission()


class DecommissionSeedNode(NemesisBaseClass):
    disruptive = True
    topology_changes = True
    supports_high_disk_utilization = False  # Decommissioning a node cause increase of disk space across rest of the nodes

    def __init__(self, runner):
        runner.disrupt_nodetool_seed_decommission()


class NoCorruptRepairMonkey(NemesisBaseClass):
    disruptive = False
    kubernetes = True
    limited = True

    def __init__(self, runner):
        runner.disrupt_no_corrupt_repair()


class MajorCompactionMonkey(NemesisBaseClass):
    disruptive = False
    kubernetes = True
    limited = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_major_compaction()


class RefreshMonkey(NemesisBaseClass):
    disruptive = False
    run_with_gemini = False
    kubernetes = True
    limited = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_nodetool_refresh(big_sstable=False)


class LoadAndStreamMonkey(NemesisBaseClass):
    disruptive = False
    run_with_gemini = False
    kubernetes = True
    limited = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_load_and_stream()


class RefreshBigMonkey(NemesisBaseClass):
    disruptive = False
    run_with_gemini = False
    kubernetes = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_nodetool_refresh(big_sstable=True)


class RemoveServiceLevelMonkey(NemesisBaseClass):
    disruptive = True
    sla = True

    def __init__(self, runner):
        runner.disrupt_remove_service_level_while_load()


class EnospcMonkey(NemesisBaseClass):
    disruptive = True
    kubernetes = True
    limited = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_nodetool_enospc()


class EnospcAllNodesMonkey(NemesisBaseClass):
    disruptive = True
    kubernetes = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_nodetool_enospc(all_nodes=True)


class NodeToolCleanupMonkey(NemesisBaseClass):
    disruptive = False
    kubernetes = True
    limited = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_nodetool_cleanup()


class TruncateMonkey(NemesisBaseClass):
    disruptive = False
    kubernetes = True
    limited = True
    free_tier_set = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_truncate()


class TruncateLargeParititionMonkey(NemesisBaseClass):
    disruptive = False
    kubernetes = True
    free_tier_set = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_truncate_large_partition()


class DeleteByPartitionsMonkey(NemesisBaseClass):
    disruptive = False
    kubernetes = True
    free_tier_set = True
    delete_rows = True

    def __init__(self, runner):
        runner.disrupt_delete_10_full_partitions()


class DeleteByRowsRangeMonkey(NemesisBaseClass):
    disruptive = False
    kubernetes = True
    free_tier_set = True
    delete_rows = True

    def __init__(self, runner):
        runner.disrupt_delete_by_rows_range()


class DeleteOverlappingRowRangesMonkey(NemesisBaseClass):
    disruptive = False
    kubernetes = True
    free_tier_set = True
    delete_rows = True

    def __init__(self, runner):
        runner.disrupt_delete_overlapping_row_ranges()


class CategoricalMonkey(Nemesis):
    """Randomly picks disruptions to execute using the given categorical distribution.

    Each disruption is assigned a weight. The probability that a disruption D with weight W
    will be executed is W / T, where T is the sum of weights of all disruptions.

    The distribution is passed into the monkey's constructor as a dictionary.
    Keys in the dictionary are names of the disruption methods (from the `Nemesis` class)
    e.g. `disrupt_hard_reboot_node`. The value for each key is the weight of this disruption.
    You can omit the ``disrupt_'' prefix from the key, e.g. `hard_reboot_node`.

    A default weight can be passed; it will be assigned to each disruption that is not listed.
    In particular if the default weight is 0 then the unlisted disruptions won't be executed.
    """

    @staticmethod
    def get_disruption_distribution(dist: dict, default_weight: float) -> Tuple[List[Callable], List[float]]:
        def is_nonnegative_number(val):
            try:
                val = float(val)
            except ValueError:
                return False
            else:
                return val >= 0

        def prefixed(pref: str, val: str) -> str:
            if val.startswith(pref):
                return val
            return pref + val

        all_methods = CategoricalMonkey.get_disrupt_methods()

        population: List[Callable] = []
        weights: List[float] = []
        listed_methods: Set[str] = set()

        for _name, _weight in dist.items():
            name = str(_name)
            prefixed_name = prefixed('disrupt_', name)
            if prefixed_name not in all_methods:
                raise ValueError(f"'{name}' is not a valid disruption. All methods: {all_methods.keys()}")

            if not is_nonnegative_number(_weight):
                raise ValueError("Each disruption weight must be a non-negative number."
                                 " '{weight}' is not a valid weight.")

            weight = float(_weight)
            if weight > 0:
                population.append(all_methods[prefixed_name])
                weights.append(weight)
            listed_methods.add(prefixed_name)

        if default_weight > 0:
            for method_name, method in all_methods.items():
                if method_name not in listed_methods:
                    population.append(method)
                    weights.append(default_weight)

        if not population:
            raise ValueError("There must be at least one disruption with a positive weight.")

        return population, weights

    @staticmethod
    def get_disrupt_methods() -> Dict[str, Callable]:
        return {attr[0]: attr[1] for attr in inspect.getmembers(CategoricalMonkey) if
                attr[0].startswith('disrupt_') and
                callable(attr[1])}

    def __init__(self, tester_obj, termination_event, dist: dict, *args, default_weight: float = 1, **kwargs):
        super().__init__(tester_obj, termination_event, *args, **kwargs)
        self.disruption_distribution = CategoricalMonkey.get_disruption_distribution(dist, default_weight)

    def disrupt(self):
        self._random_disrupt()

    def _random_disrupt(self):
        population, weights = self.disruption_distribution
        assert len(population) == len(weights) and population

        method = random.choices(population, weights=weights)[0]
        self.execute_nemesis(method)


class ScyllaCloudLimitedChaosMonkey(Nemesis):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disruptions_list = self.build_disruptions_by_name([
            'disrupt_nodetool_cleanup',
            'disrupt_nodetool_drain', 'disrupt_nodetool_refresh',
            'disrupt_stop_start_scylla_server', 'disrupt_major_compaction',
            'disrupt_modify_table', 'disrupt_nodetool_enospc',
            'disrupt_stop_wait_start_scylla_server',
            'disrupt_soft_reboot_node',
            'disrupt_truncate'
        ])
        self.shuffle_list_of_disruptions(self.disruptions_list)

    def disrupt(self):
        # Limit the nemesis scope to only one relevant to scylla cloud, where we defined we don't have AWS api access:
        self.call_next_nemesis()


class MdcChaosMonkey(Nemesis):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disruptions_list = self.build_disruptions_by_name([
            'disrupt_destroy_data_then_repair',
            'disrupt_no_corrupt_repair',
            'disrupt_nodetool_decommission'
        ])
        self.shuffle_list_of_disruptions(self.disruptions_list)

    def disrupt(self):
        self.call_next_nemesis()


class ModifyTableMonkey(NemesisBaseClass):
    disruptive = False
    kubernetes = True
    limited = True
    schema_changes = True
    free_tier_set = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_modify_table()


class AddDropColumnMonkey(NemesisBaseClass):
    disruptive = False
    run_with_gemini = False
    networking = False
    kubernetes = True
    limited = True
    schema_changes = True
    free_tier_set = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_add_drop_column()


class ToggleTableIcsMonkey(NemesisBaseClass):
    kubernetes = True
    schema_changes = True
    free_tier_set = True

    def __init__(self, runner):
        runner.disrupt_toggle_table_ics()


class ToggleGcModeMonkey(NemesisBaseClass):
    kubernetes = True
    disruptive = False
    schema_changes = True
    free_tier_set = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_toggle_table_gc_mode()


class MgmtBackup(NemesisBaseClass):
    manager_operation = True
    disruptive = False
    limited = True
    supports_high_disk_utilization = False  # Snapshot/Restore operations consume disk space

    def __init__(self, runner):
        runner.disrupt_mgmt_backup()


class MgmtBackupSpecificKeyspaces(NemesisBaseClass):
    manager_operation = True
    disruptive = False
    limited = True
    supports_high_disk_utilization = False  # Snapshot/Restore operations consume disk space

    def __init__(self, runner):
        runner.disrupt_mgmt_backup_specific_keyspaces()


class MgmtRestore(NemesisBaseClass):
    manager_operation = True
    disruptive = True
    kubernetes = True
    limited = True
    supports_high_disk_utilization = False  # Snapshot/Restore operations consume disk space

    def __init__(self, runner):
        runner.disrupt_mgmt_restore()


class MgmtRepair(NemesisBaseClass):
    manager_operation = True
    disruptive = False
    kubernetes = True
    limited = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.log.info('disrupt_mgmt_repair_cli Nemesis begin')
        runner.disrupt_mgmt_repair_cli()
        runner.log.info('disrupt_mgmt_repair_cli Nemesis end')
        # For Manager APIs test, use: runner.disrupt_mgmt_repair_api()


class MgmtCorruptThenRepair(NemesisBaseClass):
    manager_operation = True
    disruptive = True
    kubernetes = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_mgmt_corrupt_then_repair()


class AbortRepairMonkey(NemesisBaseClass):
    disruptive = False
    kubernetes = True
    limited = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_abort_repair()


class NodeTerminateAndReplace(NemesisBaseClass):
    disruptive = True
    # It should not be run on kubernetes, since it is a manual procedure
    # While on kubernetes we put it all on scylla-operator
    kubernetes = False
    topology_changes = True
    zero_node_changes = True

    def __init__(self, runner):
        runner.disrupt_terminate_and_replace_node()


class DrainKubernetesNodeThenReplaceScyllaNode(NemesisBaseClass):
    disruptive = True
    kubernetes = True

    def __init__(self, runner):
        runner.disrupt_drain_kubernetes_node_then_replace_scylla_node()


class TerminateKubernetesHostThenReplaceScyllaNode(NemesisBaseClass):
    disruptive = True
    kubernetes = True

    def __init__(self, runner):
        runner.disrupt_terminate_kubernetes_host_then_replace_scylla_node()


class DisruptKubernetesNodeThenReplaceScyllaNode(Nemesis):
    disruptive = True
    kubernetes = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disruptions_list = self.build_disruptions_by_name([
            'disrupt_drain_kubernetes_node_then_replace_scylla_node',
            'disrupt_terminate_kubernetes_host_then_replace_scylla_node',
        ])
        self.shuffle_list_of_disruptions(self.disruptions_list)

    def disrupt(self):
        self.call_next_nemesis()


class DrainKubernetesNodeThenDecommissionAndAddScyllaNode(NemesisBaseClass):
    disruptive = True
    kubernetes = True

    def __init__(self, runner):
        runner.disrupt_drain_kubernetes_node_then_decommission_and_add_scylla_node()


class TerminateKubernetesHostThenDecommissionAndAddScyllaNode(NemesisBaseClass):
    disruptive = True
    kubernetes = True

    def __init__(self, runner):
        runner.disrupt_terminate_kubernetes_host_then_decommission_and_add_scylla_node()


class DisruptKubernetesNodeThenDecommissionAndAddScyllaNode(Nemesis):
    disruptive = True
    kubernetes = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disruptions_list = self.build_disruptions_by_name([
            'disrupt_drain_kubernetes_node_then_decommission_and_add_scylla_node',
            'disrupt_terminate_kubernetes_host_then_decommission_and_add_scylla_node',
        ])
        self.shuffle_list_of_disruptions(self.disruptions_list)

    def disrupt(self):
        self.call_next_nemesis()


class K8sSetMonkey(Nemesis):
    disruptive = True
    kubernetes = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disruptions_list = self.build_disruptions_by_name([
            'disrupt_drain_kubernetes_node_then_replace_scylla_node',
            'disrupt_terminate_kubernetes_host_then_replace_scylla_node',
            'disrupt_drain_kubernetes_node_then_decommission_and_add_scylla_node',
            'disrupt_terminate_kubernetes_host_then_decommission_and_add_scylla_node',
        ])
        self.shuffle_list_of_disruptions(self.disruptions_list)

    def disrupt(self):
        self.call_next_nemesis()


class OperatorNodeReplace(NemesisBaseClass):
    disruptive = True
    kubernetes = True
    free_tier_set = True

    def __init__(self, runner):
        runner.disrupt_replace_scylla_node_on_kubernetes()


class OperatorNodetoolFlushAndReshard(NemesisBaseClass):
    disruptive = True
    kubernetes = True

    def __init__(self, runner):
        runner.disrupt_nodetool_flush_and_reshard_on_kubernetes()


class ScyllaKillMonkey(NemesisBaseClass):
    disruptive = True
    supports_high_disk_utilization = True
    kubernetes = True
    free_tier_set = True

    def __init__(self, runner):
        runner.disrupt_kill_scylla()


class ValidateHintedHandoffShortDowntime(NemesisBaseClass):
    disruptive = True
    kubernetes = True
    free_tier_set = True

    def __init__(self, runner):
        runner.disrupt_validate_hh_short_downtime()


class SnapshotOperations(NemesisBaseClass):
    disruptive = False
    kubernetes = True
    limited = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_snapshot_operations()


class NodeRestartWithResharding(NemesisBaseClass):
    disruptive = True
    kubernetes = True
    topology_changes = True
    config_changes = True

    def __init__(self, runner):
        runner.disrupt_restart_with_resharding()


class ClusterRollingRestart(NemesisBaseClass):
    disruptive = True
    supports_high_disk_utilization = True
    kubernetes = True
    free_tier_set = True

    def __init__(self, runner):
        runner.disrupt_rolling_restart_cluster(random_order=False)


class RollingRestartConfigChangeInternodeCompression(NemesisBaseClass):
    disruptive = True
    supports_high_disk_utilization = True
    full_cluster_restart = True
    config_changes = True

    def __init__(self, runner):
        runner.disrupt_rolling_config_change_internode_compression()


class ClusterRollingRestartRandomOrder(NemesisBaseClass):
    disruptive = True
    supports_high_disk_utilization = True
    kubernetes = True
    free_tier_set = True

    def __init__(self, runner):
        runner.disrupt_rolling_restart_cluster(random_order=True)


class SwitchBetweenPasswordAuthAndSaslauthdAuth(NemesisBaseClass):
    disruptive = True  # the nemesis has rolling restart
    config_changes = True

    def __init__(self, runner):
        runner.disrupt_switch_between_password_authenticator_and_saslauthd_authenticator_and_back()


class TopPartitions(NemesisBaseClass):
    disruptive = False
    kubernetes = True
    limited = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_show_toppartitions()


class RandomInterruptionNetworkMonkey(NemesisBaseClass):
    disruptive = True
    networking = True
    run_with_gemini = False
    kubernetes = True

    def __init__(self, runner):
        runner.disrupt_network_random_interruptions()


class BlockNetworkMonkey(NemesisBaseClass):
    disruptive = True
    networking = True
    run_with_gemini = False
    kubernetes = True

    def __init__(self, runner):
        runner.disrupt_network_block()


class RejectInterNodeNetworkMonkey(NemesisBaseClass):
    disruptive = True
    networking = True
    run_with_gemini = False
    free_tier_set = True

    def __init__(self, runner):
        runner.disrupt_network_reject_inter_node_communication()


class RejectNodeExporterNetworkMonkey(NemesisBaseClass):
    disruptive = True
    networking = True
    run_with_gemini = False

    def __init__(self, runner):
        runner.disrupt_network_reject_node_exporter()


class RejectThriftNetworkMonkey(NemesisBaseClass):
    disruptive = True
    networking = True
    run_with_gemini = False

    def __init__(self, runner):
        runner.disrupt_network_reject_thrift()


class StopStartInterfacesNetworkMonkey(NemesisBaseClass):
    disruptive = True
    networking = True
    run_with_gemini = False

    def __init__(self, runner):
        runner.disrupt_network_start_stop_interface()


class ScyllaOperatorBasicOperationsMonkey(Nemesis):
    """
    Selected number of nemesis that is focused on scylla-operator functionality
    """
    disruptive = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disruptions_list = self.build_disruptions_by_name([
            'disrupt_nodetool_flush_and_reshard_on_kubernetes',
            'disrupt_rolling_restart_cluster',
            'disrupt_grow_shrink_cluster',
            'disrupt_grow_shrink_new_rack',
            'disrupt_stop_start_scylla_server',
            'disrupt_drain_kubernetes_node_then_replace_scylla_node',
            'disrupt_terminate_kubernetes_host_then_replace_scylla_node',
            'disrupt_drain_kubernetes_node_then_decommission_and_add_scylla_node',
            'disrupt_terminate_kubernetes_host_then_decommission_and_add_scylla_node',
            'disrupt_replace_scylla_node_on_kubernetes',
            'disrupt_mgmt_corrupt_then_repair',
            'disrupt_mgmt_repair_cli',
            'disrupt_mgmt_backup_specific_keyspaces',
            'disrupt_mgmt_backup',
        ])
        self.shuffle_list_of_disruptions(self.disruptions_list)

    def disrupt(self):
        self.call_next_nemesis()


class NemesisSequence(NemesisBaseClass):
    disruptive = True
    networking = False
    run_with_gemini = False

    def __init__(self, runner):
        runner.disrupt_run_unique_sequence()


class TerminateAndRemoveNodeMonkey(NemesisBaseClass):
    """Remove a Node from a Scylla Cluster (Down Scale)"""
    disruptive = True
    # It should not be run on kubernetes, since it is a manual procedure
    # While on kubernetes we put it all on scylla-operator
    kubernetes = False
    topology_changes = True
    supports_high_disk_utilization = False  # Removing a node consumes disk space

    def __init__(self, runner):
        runner.disrupt_remove_node_then_add_node()


class ToggleCDCMonkey(NemesisBaseClass):
    disruptive = False
    schema_changes = True
    config_changes = True
    free_tier_set = True

    def __init__(self, runner):
        runner.disrupt_toggle_cdc_feature_properties_on_table()


class CDCStressorMonkey(NemesisBaseClass):
    disruptive = False
    free_tier_set = True

    def __init__(self, runner):
        runner.disrupt_run_cdcstressor_tool()


class DecommissionStreamingErrMonkey(NemesisBaseClass):

    disruptive = True
    topology_changes = True

    def __init__(self, runner):
        runner.disrupt_decommission_streaming_err()


class RebuildStreamingErrMonkey(NemesisBaseClass):

    disruptive = True

    def __init__(self, runner):
        runner.disrupt_rebuild_streaming_err()


class RepairStreamingErrMonkey(NemesisBaseClass):

    disruptive = True

    def __init__(self, runner):
        runner.disrupt_repair_streaming_err()


COMPLEX_NEMESIS = [NoOpMonkey, ScyllaCloudLimitedChaosMonkey,
                   MdcChaosMonkey, SisyphusMonkey,
                   DisruptKubernetesNodeThenReplaceScyllaNode,
                   DisruptKubernetesNodeThenDecommissionAndAddScyllaNode,
                   CategoricalMonkey]


class CorruptThenScrubMonkey(NemesisBaseClass):
    disruptive = False
    supports_high_disk_utilization = False  # Failed for: https://github.com/scylladb/scylladb/issues/22088

    def __init__(self, runner):
        runner.disrupt_corrupt_then_scrub()


class MemoryStressMonkey(NemesisBaseClass):
    disruptive = True
    supports_high_disk_utilization = True
    free_tier_set = True

    def __init__(self, runner):
        runner.disrupt_memory_stress()


class ResetLocalSchemaMonkey(NemesisBaseClass):
    disruptive = False
    config_changes = True
    free_tier_set = True

    def __init__(self, runner):
        runner.disrupt_resetlocalschema()


class StartStopMajorCompaction(NemesisBaseClass):
    disruptive = False
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_start_stop_major_compaction()


class StartStopScrubCompaction(NemesisBaseClass):
    disruptive = False

    def __init__(self, runner):
        runner.disrupt_start_stop_scrub_compaction()


class StartStopCleanupCompaction(NemesisBaseClass):
    disruptive = False
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_start_stop_cleanup_compaction()


class StartStopValidationCompaction(NemesisBaseClass):
    disruptive = False
    supports_high_disk_utilization = False  # Failed for: https://github.com/scylladb/scylladb/issues/22088

    def __init__(self, runner):
        runner.disrupt_start_stop_validation_compaction()


class SlaIncreaseSharesDuringLoad(NemesisBaseClass):
    disruptive = False
    sla = True

    def __init__(self, runner):
        runner.disrupt_sla_increase_shares_during_load()


class SlaDecreaseSharesDuringLoad(NemesisBaseClass):
    disruptive = False
    sla = True

    def __init__(self, runner):
        runner.disrupt_sla_decrease_shares_during_load()


class SlaReplaceUsingDetachDuringLoad(NemesisBaseClass):
    # TODO: This SLA nemesis uses binary disable/enable workaround that in a test with parallel nemeses can cause to the errors and
    #  failures that is not a problem of Scylla. The option "disruptive" was set to True to prevent irrelevant failures. Should be changed
    #  to False when the issue https://github.com/scylladb/scylla-enterprise/issues/2572 will be fixed.
    disruptive = True
    sla = True

    def __init__(self, runner):
        runner.disrupt_replace_service_level_using_detach_during_load()


class SlaReplaceUsingDropDuringLoad(NemesisBaseClass):
    # TODO: This SLA nemesis uses binary disable/enable workaround that in a test with parallel nemeses can cause to the errors and
    #  failures that is not a problem of Scylla. The option "disruptive" was set to True to prevent irrelevant failures. Should be changed
    #  to False when the issue https://github.com/scylladb/scylla-enterprise/issues/2572 will be fixed.
    disruptive = True
    sla = True

    def __init__(self, runner):
        runner.disrupt_replace_service_level_using_drop_during_load()


class SlaIncreaseSharesByAttachAnotherSlDuringLoad(NemesisBaseClass):
    # TODO: This SLA nemesis uses binary disable/enable workaround that in a test with parallel nemeses can cause to the errors and
    #  failures that is not a problem of Scylla. The option "disruptive" was set to True to prevent irrelevant failures. Should be changed
    #  to False when the issue https://github.com/scylladb/scylla-enterprise/issues/2572 will be fixed.
    disruptive = True
    sla = True

    def __init__(self, runner):
        runner.disrupt_increase_shares_by_attach_another_sl_during_load()


class SlaMaximumAllowedSlsWithMaxSharesDuringLoad(NemesisBaseClass):
    disruptive = False
    sla = True

    def __init__(self, runner):
        runner.disrupt_maximum_allowed_sls_with_max_shares_during_load()


class CreateIndexNemesis(NemesisBaseClass):

    disruptive = False
    schema_changes = True
    free_tier_set = True
    supports_high_disk_utilization = False  # Creating an Index consumes disk space

    def __init__(self, runner):
        runner.disrupt_create_index()


class AddRemoveMvNemesis(NemesisBaseClass):

    disruptive = True
    schema_changes = True
    free_tier_set = True
    supports_high_disk_utilization = False  # Creating an MV consumes disk space

    def __init__(self, runner):
        runner.disrupt_add_remove_mv()


class ToggleAuditNemesisSyslog(NemesisBaseClass):
    disruptive = True
    supports_high_disk_utilization = True
    schema_changes = True
    config_changes = True
    free_tier_set = True

    def __init__(self, runner):
        runner.disrupt_toggle_audit_syslog()


class BootstrapStreamingErrorNemesis(NemesisBaseClass):

    disruptive = True
    topology_changes = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_bootstrap_streaming_error()


class DisableBinaryGossipExecuteMajorCompaction(NemesisBaseClass):
    disruptive = True
    supports_high_disk_utilization = True
    kubernetes = True

    def __init__(self, runner):
        runner.disrupt_disable_binary_gossip_execute_major_compaction()


class EndOfQuotaNemesis(NemesisBaseClass):
    disruptive = True
    config_changes = True

    def __init__(self, runner):
        runner.disrupt_end_of_quota_nemesis()


class GrowShrinkZeroTokenNode(NemesisBaseClass):

    disruptive = True
    schema_changes = False
    free_tier_set = False
    zero_node_changes = True

    def __init__(self, runner):
        runner.disrupt_grow_shrink_zero_nodes()


class SerialRestartOfElectedTopologyCoordinatorNemesis(NemesisBaseClass):

    disruptive = True
    topology_changes = True
    supports_high_disk_utilization = True

    def __init__(self, runner):
        runner.disrupt_serial_restart_elected_topology_coordinator()


class IsolateNodeWithProcessSignalNemesis(NemesisBaseClass):
    disruptive = True
    topology_changes = True
    kubernetes = False

    def __init__(self, runner):
        runner.disrupt_refuse_connection_with_send_sigstop_signal_to_scylla_on_banned_node()


class IsolateNodeWithIptableRuleNemesis(NemesisBaseClass):
    disruptive = True
    topology_changes = True
    kubernetes = False

    def __init__(self, runner):
        runner.disrupt_refuse_connection_with_block_scylla_ports_on_banned_node()
