"""Account security: two-step sign-in, password reset, email verification, sign-out.

* user_mfa (tenant RLS): each person's authenticator secret (encrypted by the app),
  hashed recovery codes and the last accepted time step (no code reuse).
* users.password_changed_at: sign-ins issued before it stop working.
* users.email_verified_at: existing people are treated as verified.
* auth_tokens: one-time links (password reset, email verification), stored only as
  SHA-256 hashes; looked up before anyone is signed in, so not tenant-scoped.
* revoked_tokens: signed-out sessions (hashed token ids) until they would expire.

Revision ID: ff_security_002
Revises: ff_billing_001
"""

from alembic import op

revision = "ff_security_002"
down_revision = "ff_billing_001"
branch_labels = None
depends_on = None

_PREDICATE = "tenant_id = (NULLIF(current_setting('app.current_tenant_id', true), ''))::uuid"
_GRANT = (
    "DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'flowforge_app') THEN"
    " GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO flowforge_app;"
    " END IF; END $$"
)


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE user_mfa (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            created_at timestamptz NOT NULL DEFAULT now(),
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            secret varchar(300) NOT NULL,
            enabled_at timestamptz,
            recovery_codes json NOT NULL DEFAULT '[]',
            last_step bigint NOT NULL DEFAULT 0,
            CONSTRAINT uq_user_mfa UNIQUE (tenant_id, user_id)
        )
        """
    )
    op.execute("CREATE INDEX ix_user_mfa_tenant_id ON user_mfa (tenant_id)")
    op.execute("ALTER TABLE user_mfa ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_mfa FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY user_mfa_tenant_isolation ON user_mfa"
        f" FOR ALL USING ({_PREDICATE}) WITH CHECK ({_PREDICATE})"
    )
    op.execute(_GRANT.format(table="user_mfa"))
    op.execute("SELECT ff_install_same_tenant_triggers()")

    op.execute("ALTER TABLE users ADD COLUMN password_changed_at timestamptz")
    op.execute("ALTER TABLE users ADD COLUMN email_verified_at timestamptz")
    op.execute("UPDATE users SET email_verified_at = COALESCE(created_at, now())")

    op.execute(
        """
        CREATE TABLE auth_tokens (
            token_hash char(64) PRIMARY KEY,
            purpose varchar(20) NOT NULL,
            subject_tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at timestamptz NOT NULL DEFAULT now(),
            expires_at timestamptz NOT NULL,
            used_at timestamptz
        )
        """
    )
    op.execute("CREATE INDEX ix_auth_tokens_user ON auth_tokens (user_id, purpose)")
    op.execute(_GRANT.format(table="auth_tokens"))
    op.execute(
        """
        CREATE TABLE revoked_tokens (
            jti_hash char(64) PRIMARY KEY,
            expires_at timestamptz NOT NULL
        )
        """
    )
    op.execute(_GRANT.format(table="revoked_tokens"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS revoked_tokens")
    op.execute("DROP TABLE IF EXISTS auth_tokens")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS email_verified_at")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS password_changed_at")
    op.execute("DROP TABLE IF EXISTS user_mfa")
