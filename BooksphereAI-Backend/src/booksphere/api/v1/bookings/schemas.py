from __future__ import annotations

from marshmallow import Schema, fields, validate


class AvailabilityQuerySchema(Schema):
    resource_id = fields.UUID(required=True)
    service_id = fields.UUID(required=True)
    date = fields.Date(required=True)


class CreateBookingSchema(Schema):
    resource_id = fields.UUID(required=True)
    service_id = fields.UUID(required=True)
    start_time = fields.DateTime(required=True)
    notes = fields.String(required=False, allow_none=True, validate=validate.Length(max=2000))
    # Only meaningful for staff/manager/owner -- validated and
    # authorization-checked in the route, not here. A plain customer
    # sending this field has it ignored, not rejected, since a
    # well-behaved frontend simply wouldn't include it for that role.
    customer_id = fields.UUID(required=False, allow_none=True)


class BookingResponseSchema(Schema):
    id = fields.UUID()
    organization_id = fields.UUID()
    resource_id = fields.UUID()
    service_id = fields.UUID()
    customer_id = fields.UUID()
    start_time = fields.DateTime()
    end_time = fields.DateTime()
    status = fields.String()
    cancelled_at = fields.DateTime(allow_none=True)
    notes = fields.String(allow_none=True)
    created_at = fields.DateTime()
