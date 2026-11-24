from src.retrieval.cypher_generator import CypherGenerator

class CypherExecutor:
    def __init__(
        self,
        connection,
        settings,
        cypher_generator=None
    ):

        self.driver = connection.driver
        self.database = connection.database
        self.cypher_generator = (
            cypher_generator
            if cypher_generator is not None
            else CypherGenerator(settings)
        )

    # ----------------------------------
    # EXECUTE CYPHER QUERY
    # ----------------------------------

    def execute(self, query: str):

        # 1. Validate the generated query
        is_valid = self.cypher_generator.validate(query)

        if not is_valid:
            raise ValueError(
                "Unsafe or invalid Cypher query rejected."
            )

        # 2. Execute the query using a read transaction
        try:

            with self.driver.session(
                database=self.database,
                default_access_mode="READ"
            ) as session:

                result = session.execute_read(
                    self._run_query,
                    query
                )

                return result

        except Exception as error:

            print("Cypher execution failed:", error)

            return []

    # ----------------------------------
    # RUN READ QUERY
    # ----------------------------------

    @staticmethod
    def _run_query(tx, query: str):

        result = tx.run(query)

        records = [
            record.data()
            for record in result
        ]

        return records
