class CypherGuardrail:
    """
    Dedicated security layer to inspect and validate LLM-generated Cypher queries
    before they reach the active Neo4j database instance.
    """

    # Keywords that indicate data mutation or structural damage
    FORBIDDEN_KEYWORDS = [
        "create ",
        "merge ",
        "delete ",
        "set ",
        "remove ",
        "drop ",
        "detach ",
        "call apoc.import",
        "call apoc.export",
    ]

    @classmethod
    def verify_query_safety(cls, cypher_query: str) -> tuple[bool, str]:
        """
        Validates the text profile of a Cypher string.
        Returns:
            tuple: (is_safe: bool, feedback_message: str)
        """
        if not cypher_query or not isinstance(cypher_query, str):
            return False, "The query is empty or invalid."

        query_lower = cypher_query.lower()

        # 1. Look for destructive keywords
        for keyword in cls.FORBIDDEN_KEYWORDS:
            if keyword in query_lower:
                return (
                    False,
                    f"Unauthorized mutation command detected: '{keyword.strip()}'.",
                )

        # 2. Basic structural sanity check
        if "return" not in query_lower:
            return (
                False,
                "Query fails compliance check: Read-only queries must contain a RETURN clause.",
            )

        # Query passed all security gates
        return True, "Query is safe and compliant."
