from __future__ import annotations

from marshmallow import Schema, fields, validate


class CreateServiceSchema(Schema):
    name = fields.String(required=True, validate=lambda v: len(v.strip()) > 0)
    description = fields.String(required=False, allow_none=True)
    duration_minutes = fields.Integer(required=True, validate=validate.Range(min=1, max=1440))
    price_cents = fields.Integer(required=True, validate=validate.Range(min=0))
    currency = fields.String(required=False, load_default="USD", validate=validate.Length(equal=3))


class UpdateServiceSchema(Schema):
    name = fields.String(required=False, validate=lambda v: len(v.strip()) > 0)
    description = fields.String(required=False, allow_none=True)
    duration_minutes = fields.Integer(required=False, validate=validate.Range(min=1, max=1440))
    price_cents = fields.Integer(required=False, validate=validate.Range(min=0))
    currency = fields.String(required=False, validate=validate.Length(equal=3))
    is_active = fields.Boolean(required=False)


class LinkResourceSchema(Schema):
    resource_id = fields.UUID(required=True)


class ServiceResponseSchema(Schema):
    id = fields.UUID()
    organization_id = fields.UUID()
    name = fields.String()
    description = fields.String(allow_none=True)
    duration_minutes = fields.Integer()
    price_cents = fields.Integer()
    currency = fields.String()
    is_active = fields.Boolean()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
