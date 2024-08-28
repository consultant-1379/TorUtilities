from enmutils_int.lib.profile_flows.geo_r_flows.geo_r_flow import GeoRFlow


class GEO_R_01(GeoRFlow):
    """
    Use Case ID:    GEO_R
    Slogan:         Geographic Replication Solution on primary site
    """

    NAME = "GEO_R_01"

    def run(self):
        self.execute_flow()


geo_r_01 = GEO_R_01()
