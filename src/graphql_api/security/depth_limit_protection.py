"""
Query Depth Limit Protection
------------------------------
Walks the GraphQL query AST and measures maximum nesting depth.
Rejects the query before execution if depth exceeds MAX_DEPTH.

From the PDF (Part 1):
  "The server analyzes the incoming query text and measures how deeply
   the nested fields go. If a query contains more than five levels,
   the server rejects it immediately."
"""
from graphql import parse
from graphql.language.ast import FieldNode, InlineFragmentNode, FragmentSpreadNode

MAX_DEPTH = 5


def _node_depth(node, current: int) -> int:
    """Recursively compute the maximum depth from this node."""
    if isinstance(node, FieldNode):
        if node.selection_set:
            return max(
                _node_depth(child, current + 1)
                for child in node.selection_set.selections
            )
        return current
    if isinstance(node, (InlineFragmentNode,)):
        if node.selection_set:
            return max(
                _node_depth(child, current)
                for child in node.selection_set.selections
            )
        return current
    return current


def get_query_depth(query_string: str) -> int:
    """Return the maximum field nesting depth of the query."""
    try:
        doc = parse(query_string)
    except Exception:
        return 0

    max_d = 0
    for definition in doc.definitions:
        if hasattr(definition, "selection_set") and definition.selection_set:
            for selection in definition.selection_set.selections:
                max_d = max(max_d, _node_depth(selection, 1))
    return max_d


def check_depth(query_string: str, max_depth: int = MAX_DEPTH):
    """Raise ValueError if query depth exceeds max_depth."""
    depth = get_query_depth(query_string)
    if depth > max_depth:
        raise ValueError(
            f"Query depth {depth} exceeds maximum allowed depth of {max_depth}. "
            f"Reduce nesting to prevent server overload."
        )
    return depth
