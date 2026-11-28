"""Records may only reference records of their own tenant.

Foreign-key checks bypass row-level security, so before this revision a tenant could
store a reference to another tenant's record (it could not read it, but the reference
was accepted). This revision adds:

* ff_check_same_tenant(): a trigger function that, for each (column, referenced table)
  pair passed as arguments, requires the referenced row to belong to NEW.tenant_id.
  Violations raise SQLSTATE 23503 (foreign_key_violation), which the API reports as a
  conflict like any other invalid reference.
* ff_install_same_tenant_triggers(): (re)creates trigger ff_same_tenant on every table
  whose single-column foreign keys point from a tenant table to another tenant table's
  id. Later migrations that add tables call it again; a test enforces full coverage.

Production was checked before this revision: no cross-tenant references existed.

Revision ID: ff_security_001
Revises: ff_rbac_002
"""

from alembic import op

revision = "ff_security_001"
down_revision = "ff_rbac_002"
branch_labels = None
depends_on = None

CHECK_FUNCTION = r"""
CREATE OR REPLACE FUNCTION ff_check_same_tenant() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    i integer;
    col text;
    ref text;
    new_value uuid;
    old_value uuid;
    found boolean;
BEGIN
    FOR i IN 0 .. (TG_NARGS / 2) - 1 LOOP
        col := TG_ARGV[i * 2];
        ref := TG_ARGV[i * 2 + 1];
        EXECUTE format('SELECT ($1).%I::uuid', col) USING NEW INTO new_value;
        CONTINUE WHEN new_value IS NULL;
        IF TG_OP = 'UPDATE' THEN
            EXECUTE format('SELECT ($1).%I::uuid', col) USING OLD INTO old_value;
            CONTINUE WHEN old_value IS NOT DISTINCT FROM new_value
                AND OLD.tenant_id IS NOT DISTINCT FROM NEW.tenant_id;
        END IF;
        EXECUTE format('SELECT EXISTS (SELECT 1 FROM %I WHERE id = $1 AND tenant_id = $2)', ref)
            USING new_value, NEW.tenant_id INTO found;
        IF NOT found THEN
            RAISE EXCEPTION USING
                ERRCODE = 'foreign_key_violation',
                MESSAGE = format('%s.%s must reference a %s record of the same tenant',
                                 TG_TABLE_NAME, col, ref);
        END IF;
    END LOOP;
    RETURN NEW;
END;
$$;
"""

INSTALL_FUNCTION = r"""
CREATE OR REPLACE FUNCTION ff_install_same_tenant_triggers() RETURNS integer
LANGUAGE plpgsql AS $$
DECLARE
    t record;
    installed integer := 0;
BEGIN
    FOR t IN
        SELECT c.conrelid::regclass::text AS tbl,
               string_agg(
                   quote_literal(a.attname) || ', ' || quote_literal(c.confrelid::regclass::text),
                   ', ' ORDER BY a.attname
               ) AS args
        FROM pg_constraint c
        JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]
        JOIN pg_attribute ra ON ra.attrelid = c.confrelid AND ra.attnum = c.confkey[1]
        WHERE c.contype = 'f'
          AND array_length(c.conkey, 1) = 1
          AND c.connamespace = 'public'::regnamespace
          AND ra.attname = 'id'
          AND c.confrelid::regclass::text <> 'tenants'
          AND EXISTS (SELECT 1 FROM pg_attribute x WHERE x.attrelid = c.conrelid
                      AND x.attname = 'tenant_id' AND NOT x.attisdropped)
          AND EXISTS (SELECT 1 FROM pg_attribute x WHERE x.attrelid = c.confrelid
                      AND x.attname = 'tenant_id' AND NOT x.attisdropped)
        GROUP BY c.conrelid
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS ff_same_tenant ON %I', t.tbl);
        EXECUTE format(
            'CREATE TRIGGER ff_same_tenant BEFORE INSERT OR UPDATE ON %I '
            'FOR EACH ROW EXECUTE FUNCTION ff_check_same_tenant(%s)', t.tbl, t.args);
        installed := installed + 1;
    END LOOP;
    RETURN installed;
END;
$$;
"""


def upgrade() -> None:
    op.execute(CHECK_FUNCTION)
    op.execute(INSTALL_FUNCTION)
    op.execute("SELECT ff_install_same_tenant_triggers()")


def downgrade() -> None:
    op.execute(
        """
        DO $$
        DECLARE t record;
        BEGIN
            FOR t IN SELECT tgrelid::regclass::text AS tbl FROM pg_trigger
                     WHERE tgname = 'ff_same_tenant' AND NOT tgisinternal
            LOOP
                EXECUTE format('DROP TRIGGER IF EXISTS ff_same_tenant ON %I', t.tbl);
            END LOOP;
        END $$;
        """
    )
    op.execute("DROP FUNCTION IF EXISTS ff_install_same_tenant_triggers()")
    op.execute("DROP FUNCTION IF EXISTS ff_check_same_tenant()")
