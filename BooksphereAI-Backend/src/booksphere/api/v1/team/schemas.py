from __future__ import annotations
from marshmallow import Schema, fields, validate


class CreateInviteSchema(Schema):
    email = fields.Email(required=True)
    role = fields.String(required=True)


class InviteResponseSchema(Schema):
    id = fields.UUID()
    organization_id = fields.UUID()
    email = fields.Email()
    role = fields.String()
    status = fields.String()
    expires_at = fields.DateTime()
    created_at = fields.DateTime()


class InvitePreviewSchema(Schema):
    """Public-facing preview, shown before the invitee logs in/accepts.
    Deliberately minimal -- no internal IDs beyond what's needed to
    render 'You've been invited to join X as a Y'."""
    organization_name = fields.String(attribute="organization.name")
    role = fields.String()
    email = fields.Email()
    expires_at = fields.DateTime()


class ChangeRoleSchema(Schema):
    role = fields.String(required=True)


class MemberResponseSchema(Schema):
    user_id = fields.UUID()
    role = fields.String()
    email = fields.Email(attribute="user.email")
    full_name = fields.String(attribute="user.full_name")
    joined_at = fields.DateTime(attribute="created_at")
