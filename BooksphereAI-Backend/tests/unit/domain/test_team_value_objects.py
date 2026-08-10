from __future__ import annotations
import pytest

from booksphere.domain.team.exceptions import CannotModifyOwnerRoleError, InvalidRoleError
from booksphere.domain.team.value_objects import validate_assignable_role


class TestValidateAssignableRole:
    def test_accepts_manager(self):
        validate_assignable_role("manager")  # should not raise

    def test_accepts_staff(self):
        validate_assignable_role("staff")

    def test_accepts_customer(self):
        validate_assignable_role("customer")

    def test_rejects_owner_with_specific_error(self):
        """Attempting to grant 'owner' must raise the SPECIFIC
        CannotModifyOwnerRoleError, not a generic InvalidRoleError --
        the distinction matters because it signals a deliberate
        design boundary (ownership transfer isn't supported yet), not
        a typo/validation failure."""
        with pytest.raises(CannotModifyOwnerRoleError):
            validate_assignable_role("owner")

    def test_rejects_unknown_role(self):
        with pytest.raises(InvalidRoleError):
            validate_assignable_role("superadmin")
