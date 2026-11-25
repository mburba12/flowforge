TENANT_SETTING = "app.current_tenant_id"


def rls_sql(table_name: str) -> str:
    safe = table_name.replace('"', "")
    policy = f"{safe}_tenant_isolation"

    tenant_expression = f"NULLIF(current_setting('{TENANT_SETTING}', true), '')::uuid"

    return (
        f'ALTER TABLE "{safe}" '
        "ENABLE ROW LEVEL SECURITY;\n"
        f'ALTER TABLE "{safe}" '
        "FORCE ROW LEVEL SECURITY;\n"
        f'DROP POLICY IF EXISTS "{policy}" '
        f'ON "{safe}";\n'
        f'CREATE POLICY "{policy}" '
        f'ON "{safe}" FOR ALL\n'
        f"USING (tenant_id = {tenant_expression})\n"
        f"WITH CHECK "
        f"(tenant_id = {tenant_expression});"
    )
