from enmutils_int.lib.profile_flows.fs_quotas_flows.fs_quotas_flow import FsQuotas01Flow


class FS_QUOTAS_01(FsQuotas01Flow):
    """
    Use Case ID:    FS_QUOTAS_1
    Slogan:    Create ceph quota for a specific user
    """
    NAME = "FS_QUOTAS_01"

    def run(self):
        self.execute_flow()


fs_quotas_01 = FS_QUOTAS_01()
