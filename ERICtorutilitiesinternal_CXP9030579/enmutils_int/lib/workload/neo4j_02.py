from enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow import Neo4JProfile02


class NEO4J_02(Neo4JProfile02):
    """
    Use Case ID:        Neo4j_02
    Slogan:              NEO4J_02 that takes the NEO4J leader out of the cluster for 6 hours every Monday.
    """

    NAME = "NEO4J_02"

    def run(self):
        self.execute_flow()


neo4j_02 = NEO4J_02()
