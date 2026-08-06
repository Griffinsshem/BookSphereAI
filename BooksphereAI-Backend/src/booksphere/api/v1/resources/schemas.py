from __future__ import annotations

from marshmallow import Schema, fields, validate


class CreateResourceSchema(Schema):
    resource_type = fields.String(required=True)
    name = fields.String(required=True, validate=lambda v: len(v.strip()) > 0)
    description = fields.String(required=False, allow_none=True)
    capacity = fields.Integer(required=False, allow_none=True, validate=validate.Range(min=1))
    user_id = fields.UUID(required=False, allow_none=True)


class UpdateResourceSchema(Schema):
    # Every field optional -- PATCH semantics. is_active included so
    # this schema can also handle explicit reactivation, not just the
    # dedicated deactivate endpoint.
    name = fields.String(required=False, validate=lambda v: len(v.strip()) > 0)
    description = fields.String(required=False, allow_none=True)
    capacity = fields.Integer(required=False, allow_none=True, validate=validate.Range(min=1))
    is_active = fields.Boolean(required=False)


class CreateWorkingHoursSchema(Schema):
    day_of_week = fields.Integer(required=True, validate=validate.Range(min=0, max=6))
    start_time = fields.Time(required=True)
    end_time = fields.Time(required=True)


class ResourceResponseSchema(Schema):
    id = fields.UUID()
    organization_id = fields.UUID()
    resource_type = fields.String()
    user_id = fields.UUID(allow_none=True)
    name = fields.String()
    description = fields.String(allow_none=True)
    capacity = fields.Integer(allow_none=True)
    is_active = fields.Boolean()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class WorkingHoursResponseSchema(Schema):
    id = fields.UUID()
    resource_id = fields.UUID()
    day_of_week = fields.Integer()
    start_time = fields.Time()
    end_time = fields.Time()
