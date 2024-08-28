from enmutils_int.lib.profile_flows.neo4j_flows.neo4j_flow import Neo4JProfile01


class NEO4J_01(Neo4JProfile01):
    """
    Use Case ID:        Neo4j_01
    Slogan:             DB Replication
    """

    NAME = "NEO4J_01"

    def run(self):
        self.execute_flow()


neo4j_01 = NEO4J_01()
