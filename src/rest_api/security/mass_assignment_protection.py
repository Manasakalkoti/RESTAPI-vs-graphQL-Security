"""
Mass Assignment Protection
---------------------------
Defines an explicit allowlist of fields a client may update.
All other fields in the incoming JSON are silently discarded.

From the PDF:
  "The server does not forward the entire request directly to the database.
   Instead, it manually selects only approved fields that are safe to update."
"""

ALLOWED_USER_UPDATE_FIELDS = {"username", "email", "bio"}


def filter_allowed_fields(data: dict, allowed: set) -> dict:
    """Return only the keys in `data` that appear in `allowed`."""
    return {k: v for k, v in data.items() if k in allowed}
