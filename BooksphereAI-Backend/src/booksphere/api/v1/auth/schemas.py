"""
Request/response validation for the auth endpoints.

Marshmallow schemas are the validation layer — routes never inspect
request.json directly, and response serialization is an explicit
allow-list of fields (so password_hash, for instance, can never
accidentally leak even if a future refactor changes what the route
passes in).
"""
from __future__ import annotations

from marshmallow import Schema, ValidationError, fields, validates

from booksphere.domain.users.value_objects import is_password_strong_enough


class RegisterRequestSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
    full_name = fields.String(required=True, validate=lambda v: len(v.strip()) > 0)
    organization_name = fields.String(
        required=True, validate=lambda v: len(v.strip()) > 0
    )

    @validates("password")
    def validate_password_strength(self, value: str, **kwargs: object) -> None:
        if not is_password_strong_enough(value):
            raise ValidationError(
                "Password must be at least 12 characters and include a "
                "letter and a number."
            )


class LoginRequestSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)


class UserResponseSchema(Schema):
    id = fields.UUID()
    email = fields.Email()
    full_name = fields.String()
    email_verified = fields.Boolean()
    created_at = fields.DateTime()


class OrganizationResponseSchema(Schema):
    id = fields.UUID()
    name = fields.String()
    slug = fields.String()
    timezone = fields.String()


class MembershipResponseSchema(Schema):
    organization = fields.Nested(OrganizationResponseSchema)
    role = fields.String()


class AuthResponseSchema(Schema):
    user = fields.Nested(UserResponseSchema)
    access_token = fields.String()
