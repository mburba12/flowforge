"""phase 4s1 authorization tenant hardening

Revision ID: 4726038422d0
Revises: 149f3d7edf78
"""

import sqlalchemy as sa
from alembic import op

revision = "4726038422d0"
down_revision = "149f3d7edf78"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_users_tenant_id_id",
        "users",
        ["tenant_id", "id"],
    )
    op.create_unique_constraint(
        "uq_roles_tenant_id_id",
        "roles",
        ["tenant_id", "id"],
    )

    # Add nullable columns first so existing rows
    # can be assigned to their proper tenants.
    op.add_column(
        "user_roles",
        sa.Column(
            "tenant_id",
            sa.Uuid(),
            nullable=True,
        ),
    )
    op.add_column(
        "role_permissions",
        sa.Column(
            "tenant_id",
            sa.Uuid(),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE user_roles AS ur
        SET tenant_id = u.tenant_id
        FROM users AS u
        WHERE u.id = ur.user_id
        """
    )

    op.execute(
        """
        UPDATE role_permissions AS rp
        SET tenant_id = r.tenant_id
        FROM roles AS r
        WHERE r.id = rp.role_id
        """
    )

    # Abort instead of creating unowned
    # authorization relationships.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM user_roles
                WHERE tenant_id IS NULL
            ) THEN
                RAISE EXCEPTION
                    'Unowned user_roles row';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM role_permissions
                WHERE tenant_id IS NULL
            ) THEN
                RAISE EXCEPTION
                    'Unowned role_permissions row';
            END IF;
        END
        $$;
        """
    )

    op.alter_column(
        "user_roles",
        "tenant_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
    op.alter_column(
        "role_permissions",
        "tenant_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )

    op.create_index(
        "ix_user_roles_tenant_id",
        "user_roles",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_role_permissions_tenant_id",
        "role_permissions",
        ["tenant_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_user_roles_tenant_id_tenants",
        "user_roles",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_role_permissions_tenant_id_tenants",
        "role_permissions",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # These composite constraints prevent a user,
    # role, or authorization assignment from
    # crossing tenant boundaries.
    op.create_foreign_key(
        "fk_user_roles_tenant_user",
        "user_roles",
        "users",
        ["tenant_id", "user_id"],
        ["tenant_id", "id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_user_roles_tenant_role",
        "user_roles",
        "roles",
        ["tenant_id", "role_id"],
        ["tenant_id", "id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_role_permissions_tenant_role",
        "role_permissions",
        "roles",
        ["tenant_id", "role_id"],
        ["tenant_id", "id"],
        ondelete="CASCADE",
    )

    op.create_unique_constraint(
        "uq_user_roles_tenant_user_role",
        "user_roles",
        [
            "tenant_id",
            "user_id",
            "role_id",
        ],
    )
    op.create_unique_constraint(
        "uq_role_permissions_tenant_role_permission",
        "role_permissions",
        [
            "tenant_id",
            "role_id",
            "permission_id",
        ],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_role_permissions_tenant_role_permission",
        "role_permissions",
        type_="unique",
    )
    op.drop_constraint(
        "uq_user_roles_tenant_user_role",
        "user_roles",
        type_="unique",
    )

    op.drop_constraint(
        "fk_role_permissions_tenant_role",
        "role_permissions",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_user_roles_tenant_role",
        "user_roles",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_user_roles_tenant_user",
        "user_roles",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_role_permissions_tenant_id_tenants",
        "role_permissions",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_user_roles_tenant_id_tenants",
        "user_roles",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_role_permissions_tenant_id",
        table_name="role_permissions",
    )
    op.drop_index(
        "ix_user_roles_tenant_id",
        table_name="user_roles",
    )

    op.drop_column(
        "role_permissions",
        "tenant_id",
    )
    op.drop_column(
        "user_roles",
        "tenant_id",
    )

    op.drop_constraint(
        "uq_roles_tenant_id_id",
        "roles",
        type_="unique",
    )
    op.drop_constraint(
        "uq_users_tenant_id_id",
        "users",
        type_="unique",
    )
