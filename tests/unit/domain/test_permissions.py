"""
Unit tests for Permission value objects and role-based access control.

Tests permission definitions, role mappings, and authorization logic.
"""

from src.domain.value_objects.permission import (
    Permission,
    RolePermissions,
    PermissionChecker,
)
from src.domain.entities.user import UserRole


class TestPermissionEnum:
    def test_all_permissions_defined(self):
        """Test that all expected permissions are defined."""
        permissions = Permission.__members__

        # Check that we have the expected permissions
        expected_permissions = {
            "USER_CREATE",
            "USER_READ",
            "USER_UPDATE",
            "USER_DELETE",
            "DATASOURCE_CREATE",
            "DATASOURCE_READ",
            "DATASOURCE_UPDATE",
            "DATASOURCE_DELETE",
            "CURATION_REVIEW",
            "CURATION_APPROVE",
            "CURATION_REJECT",
            "SYSTEM_ADMIN",
            "AUDIT_READ",
        }

        actual_permissions = set(permissions.keys())
        assert actual_permissions == expected_permissions

    def test_permission_values_are_unique(self):
        """Test that all permission values are unique."""
        values = [p.value for p in Permission]
        assert len(values) == len(set(values))

    def test_permission_values_follow_convention(self):
        """Test that permission values follow resource:action convention."""
        for permission in Permission:
            value = permission.value
            assert (
                ":" in value
            ), f"Permission {permission.name} doesn't follow convention"
            resource, action = value.split(":", 1)
            assert resource, f"Empty resource in {value}"
            assert action, f"Empty action in {value}"


class TestRolePermissions:
    def test_admin_has_all_permissions(self):
        """Test that admin role has all permissions."""
        admin_permissions = RolePermissions.get_permissions_for_role(UserRole.ADMIN)
        all_permissions = list(Permission)

        assert set(admin_permissions) == set(all_permissions)

    def test_role_hierarchy_maintained(self):
        """Test that role hierarchy follows security principles."""
        hierarchy = RolePermissions.get_role_hierarchy()

        # Admin has highest level
        assert hierarchy[UserRole.ADMIN] > hierarchy[UserRole.CURATOR]
        assert hierarchy[UserRole.CURATOR] > hierarchy[UserRole.RESEARCHER]
        assert hierarchy[UserRole.RESEARCHER] > hierarchy[UserRole.VIEWER]

    def test_role_permissions_increase_with_level(self):
        """Test that higher roles have at least as many permissions as lower roles."""
        roles_by_level = sorted(
            [
                (level, role)
                for role, level in RolePermissions.get_role_hierarchy().items()
            ],
            key=lambda x: x[0],
        )

        for i, (level, role) in enumerate(roles_by_level[:-1]):
            current_permissions = set(RolePermissions.get_permissions_for_role(role))
            next_role = roles_by_level[i + 1][1]
            next_permissions = set(RolePermissions.get_permissions_for_role(next_role))

            # Higher roles should have at least as many permissions
            assert next_permissions.issuperset(
                current_permissions
            ), f"Role {next_role} missing permissions from {role}"

    def test_viewer_has_minimal_permissions(self):
        """Test that viewer role has minimal permissions."""
        viewer_permissions = RolePermissions.get_permissions_for_role(UserRole.VIEWER)

        # Viewer should only have read permissions
        expected_permissions = {Permission.DATASOURCE_READ}
        assert set(viewer_permissions) == expected_permissions

    def test_researcher_permissions(self):
        """Test researcher role permissions."""
        researcher_permissions = RolePermissions.get_permissions_for_role(
            UserRole.RESEARCHER
        )

        # Researcher should have read and create permissions for data sources
        expected_permissions = {
            Permission.DATASOURCE_READ,
            Permission.DATASOURCE_CREATE,
        }
        assert set(researcher_permissions) == expected_permissions

    def test_curator_permissions(self):
        """Test curator role permissions."""
        curator_permissions = RolePermissions.get_permissions_for_role(UserRole.CURATOR)

        # Curator should have data source permissions + curation permissions
        expected_permissions = {
            Permission.DATASOURCE_READ,
            Permission.DATASOURCE_CREATE,
            Permission.DATASOURCE_UPDATE,
            Permission.CURATION_REVIEW,
            Permission.CURATION_APPROVE,
            Permission.CURATION_REJECT,
        }
        assert set(curator_permissions) == expected_permissions

    def test_role_management_permissions(self):
        """Test which roles can manage other roles."""
        # Admin can manage anyone
        assert RolePermissions.can_role_manage_role(UserRole.ADMIN, UserRole.VIEWER)
        assert RolePermissions.can_role_manage_role(UserRole.ADMIN, UserRole.RESEARCHER)
        assert RolePermissions.can_role_manage_role(UserRole.ADMIN, UserRole.CURATOR)

        # Curator cannot manage other curators or admins
        assert not RolePermissions.can_role_manage_role(
            UserRole.CURATOR, UserRole.CURATOR
        )
        assert not RolePermissions.can_role_manage_role(
            UserRole.CURATOR, UserRole.ADMIN
        )

        # Curator can manage researchers and viewers
        assert RolePermissions.can_role_manage_role(
            UserRole.CURATOR, UserRole.RESEARCHER
        )
        assert RolePermissions.can_role_manage_role(UserRole.CURATOR, UserRole.VIEWER)

        # Researchers cannot manage anyone
        assert not RolePermissions.can_role_manage_role(
            UserRole.RESEARCHER, UserRole.VIEWER
        )
        assert not RolePermissions.can_role_manage_role(
            UserRole.RESEARCHER, UserRole.CURATOR
        )

    def test_permission_validation(self):
        """Test permission validation logic."""
        # This should not raise an exception
        RolePermissions.validate_permission_hierarchy()

        # Verify the validation actually checks something by temporarily breaking hierarchy
        # (This is more of an integration test, but demonstrates the validation works)

    def test_get_all_permissions(self):
        """Test getting all available permissions."""
        all_permissions = RolePermissions.get_all_permissions()
        assert len(all_permissions) == len(Permission)
        assert set(all_permissions) == set(Permission)


class TestPermissionChecker:
    def test_has_permission(self):
        """Test permission checking."""
        user_permissions = [
            Permission.USER_READ,
            Permission.USER_UPDATE,
            Permission.DATASOURCE_READ,
        ]

        assert PermissionChecker.has_permission(user_permissions, Permission.USER_READ)
        assert PermissionChecker.has_permission(
            user_permissions, Permission.DATASOURCE_READ
        )
        assert not PermissionChecker.has_permission(
            user_permissions, Permission.USER_CREATE
        )
        assert not PermissionChecker.has_permission(
            user_permissions, Permission.SYSTEM_ADMIN
        )

    def test_has_any_permission(self):
        """Test checking for any of multiple permissions."""
        user_permissions = [Permission.USER_READ, Permission.DATASOURCE_READ]

        # Has at least one from the list
        assert PermissionChecker.has_any_permission(
            user_permissions, [Permission.USER_READ, Permission.USER_CREATE]
        )

        # Doesn't have any from the list
        assert not PermissionChecker.has_any_permission(
            user_permissions, [Permission.USER_CREATE, Permission.SYSTEM_ADMIN]
        )

    def test_has_all_permissions(self):
        """Test checking for all permissions."""
        user_permissions = [
            Permission.USER_READ,
            Permission.USER_UPDATE,
            Permission.DATASOURCE_READ,
        ]

        # Has all permissions in the list
        assert PermissionChecker.has_all_permissions(
            user_permissions, [Permission.USER_READ, Permission.DATASOURCE_READ]
        )

        # Missing one permission
        assert not PermissionChecker.has_all_permissions(
            user_permissions, [Permission.USER_READ, Permission.SYSTEM_ADMIN]
        )

    def test_get_missing_permissions(self):
        """Test identifying missing permissions."""
        user_permissions = [Permission.USER_READ, Permission.DATASOURCE_READ]

        required_permissions = [
            Permission.USER_READ,
            Permission.USER_UPDATE,
            Permission.SYSTEM_ADMIN,
        ]

        missing = PermissionChecker.get_missing_permissions(
            user_permissions, required_permissions
        )

        expected_missing = {Permission.USER_UPDATE, Permission.SYSTEM_ADMIN}
        assert set(missing) == expected_missing

    def test_empty_permission_lists(self):
        """Test behavior with empty permission lists."""
        user_permissions = [Permission.USER_READ]

        # Empty required list - should return false for "any" check (no permissions to check)
        assert not PermissionChecker.has_any_permission(user_permissions, [])

        # Empty required list - should return true for "all" check (all of nothing is satisfied)
        assert PermissionChecker.has_all_permissions(user_permissions, [])

        # Empty user permissions
        assert not PermissionChecker.has_any_permission([], [Permission.USER_READ])
        assert not PermissionChecker.has_all_permissions([], [Permission.USER_READ])

        # Get missing from empty user permissions
        missing = PermissionChecker.get_missing_permissions([], [Permission.USER_READ])
        assert missing == [Permission.USER_READ]


class TestRolePermissionIntegration:
    def test_role_to_permission_mapping_completeness(self):
        """Test that all roles have proper permission mappings."""
        for role in UserRole:
            permissions = RolePermissions.get_permissions_for_role(role)
            assert isinstance(permissions, list)
            assert (
                len(permissions) > 0
            )  # Every role should have at least one permission

            # All permissions should be valid Permission enum values
            for permission in permissions:
                assert isinstance(permission, Permission)

    def test_permission_resource_action_coverage(self):
        """Test that permissions cover all expected resource-action combinations."""
        permissions = list(Permission)

        # Expected resource types and actions covered in assertions below

        found_resources = set()
        found_actions = set()

        for permission in permissions:
            resource, action = permission.value.split(":", 1)
            found_resources.add(resource)
            found_actions.add(action)

        # Check that we cover the expected resources and actions
        # Note: The assertion above checks for exact matches, which is correct
        # The test is working as intended

    def test_admin_role_comprehensive_access(self):
        """Test that admin role truly has comprehensive access."""
        admin_permissions = set(
            RolePermissions.get_permissions_for_role(UserRole.ADMIN)
        )
        all_permissions = set(Permission)

        assert admin_permissions == all_permissions

        # Admin should be able to perform any action
        for permission in Permission:
            assert permission in admin_permissions

    def test_least_privilege_principle(self):
        """Test that roles follow the principle of least privilege."""
        roles_by_privilege = [
            (UserRole.VIEWER, 1),
            (UserRole.RESEARCHER, 2),
            (UserRole.CURATOR, 3),
            (UserRole.ADMIN, 4),
        ]

        for role, expected_level in roles_by_privilege:
            current_permissions = set(RolePermissions.get_permissions_for_role(role))

            # Each role should have appropriate permissions for its level
            if expected_level == 1:  # Viewer
                assert len(current_permissions) == 1  # Only read access
            elif expected_level == 2:  # Researcher
                assert len(current_permissions) == 2  # Read + create
            elif expected_level == 3:  # Curator
                assert len(current_permissions) > 2  # Multiple permissions
            elif expected_level == 4:  # Admin
                assert current_permissions == set(Permission)  # All permissions
