"""
Query Complexity / Budget Protection
--------------------------------------
Assigns a cost to each field type and rejects queries whose total cost
exceeds MAX_COMPLEXITY.  This stops alias/batching attacks where many
expensive operations are packed into one HTTP request.

From the PDF (Part 1):
  "The server assigns a cost or weight to operations inside a query.
   If the total cost exceeds the allowed limit, the server rejects
   the request immediately."
"""
from graphql import parse
from graphql.language.ast import FieldNode, InlineFragmentNode

MAX_COMPLEXITY = 100

# Cost per field name — higher for auth/list operations
FIELD_COSTS: dict = {
    "login": 20,
    "register": 15,
    "users": 10,
    "posts": 10,
    "orders": 10,
    "user": 5,
    "post": 5,
    "order": 5,
}
DEFAULT_COST = 1


def _node_cost(node) -> int:
    if isinstance(node, FieldNode):
        name = node.name.value
        cost = FIELD_COSTS.get(name, DEFAULT_COST)
        if node.selection_set:
            cost += sum(_node_cost(c) for c in node.selection_set.selections)
        return cost
    if isinstance(node, InlineFragmentNode):
        if node.selection_set:
            return sum(_node_cost(c) for c in node.selection_set.selections)
        return 0
    return 0


def get_query_complexity(query_string: str) -> int:
    """Return the total complexity score of the query."""
    try:
        doc = parse(query_string)
    except Exception:
        return 0

    total = 0
    for definition in doc.definitions:
        if hasattr(definition, "selection_set") and definition.selection_set:
            for selection in definition.selection_set.selections:
                total += _node_cost(selection)
    return total


def check_complexity(query_string: str, max_complexity: int = MAX_COMPLEXITY):
    """Raise ValueError if query complexity exceeds max_complexity."""
    complexity = get_query_complexity(query_string)
    if complexity > max_complexity:
        raise ValueError(
            f"Query complexity {complexity} exceeds budget of {max_complexity}. "
            f"Split the request or reduce the number of aliased operations."
        )
    return complexity
