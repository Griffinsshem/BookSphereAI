from __future__ import annotations
from marshmallow import Schema, fields


class UpdateOrganizationSchema(Schema):
    timezone = fields.String(required=True)


class OrganizationDetailSchema(Schema):
    id = fields.UUID()
    name = fields.String()
    slug = fields.String()
    timezone = fields.String()
