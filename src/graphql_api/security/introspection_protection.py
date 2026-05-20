"""
Introspection Protection
-------------------------
Checks whether the incoming GraphQL query is an introspection query
(__schema / __type) and rejects it when introspection is disabled.

From the PDF (Part 1):
  "When the setting is disabled, normal application requests still work.
   However, if someone tries to ask for schema details, the server
   immediately blocks the request."
"""


def is_introspection_query(query: str) -> bool:
    """Return True if the query string contains introspection keywords."""
    q = query.strip()
    return "__schema" in q or "__type" in q
