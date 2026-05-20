"""
Excessive Data Exposure Protection
------------------------------------
Marshmallow schemas that define a safe public representation of each model.
Sensitive fields (password_hash, is_admin, reset_token, internal_notes)
are excluded at the serialisation layer and never sent to the client.

From the PDF:
  "The backend defines a limited public representation of each object.
   Sensitive information such as passwords, hidden identifiers, or private
   records are excluded completely before the response is prepared."
"""
from marshmallow import Schema, fields


class PublicUserSchema(Schema):
    id = fields.Int()
    username = fields.Str()
    email = fields.Str()
    bio = fields.Str()
    # password_hash   — omitted intentionally
    # is_admin        — omitted intentionally
    # reset_token     — omitted intentionally
    # internal_notes  — omitted intentionally


class PublicOrderSchema(Schema):
    id = fields.Int()
    item_name = fields.Str()
    amount = fields.Float()
    # user_id         — omitted (no need to echo back)
    # internal_notes  — omitted intentionally


public_user_schema = PublicUserSchema()
public_order_schema = PublicOrderSchema()
public_orders_schema = PublicOrderSchema(many=True)
