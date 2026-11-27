\set ON_ERROR_STOP on

SELECT
    current_user,
    current_setting('is_superuser'),
    current_setting('row_security');

DO $isolation$
DECLARE
    tenant_ids uuid[] := ARRAY[
        'f0000000-0000-4000-8000-000000000001'::uuid,
        'f0000000-0000-4000-8000-000000000002'::uuid,
        'f0000000-0000-4000-8000-000000000003'::uuid,
        'f0000000-0000-4000-8000-000000000004'::uuid
    ];
    expected_codes text[] := ARRAY[
        'ALPHA-ONLY',
        'BRAVO-ONLY',
        'CHARLIE-ONLY',
        'DELTA-ONLY'
    ];
    current_tenant uuid;
    own_count integer;
    foreign_count integer;
    affected_count integer;
    visible_code text;
    index_number integer;
    other_index integer;
BEGIN
    PERFORM set_config('app.current_tenant_id', '', false);

    SELECT COUNT(*)
    INTO own_count
    FROM organization_units
    WHERE id IN (
        'f1000000-0000-4000-8000-000000000001',
        'f1000000-0000-4000-8000-000000000002',
        'f1000000-0000-4000-8000-000000000003',
        'f1000000-0000-4000-8000-000000000004'
    );

    IF own_count <> 0 THEN
        RAISE EXCEPTION
            'FAIL: no-context query exposed % fixture rows',
            own_count;
    END IF;

    RAISE NOTICE 'PASS: no tenant context exposes zero rows';

    FOR index_number IN 1..4 LOOP
        current_tenant := tenant_ids[index_number];

        PERFORM set_config(
            'app.current_tenant_id',
            current_tenant::text,
            false
        );

        SELECT COUNT(*), MIN(code)
        INTO own_count, visible_code
        FROM organization_units
        WHERE id IN (
            'f1000000-0000-4000-8000-000000000001',
            'f1000000-0000-4000-8000-000000000002',
            'f1000000-0000-4000-8000-000000000003',
            'f1000000-0000-4000-8000-000000000004'
        );

        IF own_count <> 1 THEN
            RAISE EXCEPTION
                'FAIL: tenant % sees % fixture rows instead of 1',
                current_tenant,
                own_count;
        END IF;

        IF visible_code <> expected_codes[index_number] THEN
            RAISE EXCEPTION
                'FAIL: tenant % sees code % instead of %',
                current_tenant,
                visible_code,
                expected_codes[index_number];
        END IF;

        SELECT COUNT(*)
        INTO foreign_count
        FROM organization_units
        WHERE tenant_id <> current_tenant
          AND id IN (
              'f1000000-0000-4000-8000-000000000001',
              'f1000000-0000-4000-8000-000000000002',
              'f1000000-0000-4000-8000-000000000003',
              'f1000000-0000-4000-8000-000000000004'
          );

        IF foreign_count <> 0 THEN
            RAISE EXCEPTION
                'FAIL: tenant % sees % foreign rows',
                current_tenant,
                foreign_count;
        END IF;

        FOR other_index IN 1..4 LOOP
            IF other_index = index_number THEN
                CONTINUE;
            END IF;

            UPDATE organization_units
            SET name = 'CROSS-TENANT UPDATE SHOULD FAIL'
            WHERE tenant_id = tenant_ids[other_index]
              AND id IN (
                  'f1000000-0000-4000-8000-000000000001',
                  'f1000000-0000-4000-8000-000000000002',
                  'f1000000-0000-4000-8000-000000000003',
                  'f1000000-0000-4000-8000-000000000004'
              );

            GET DIAGNOSTICS affected_count = ROW_COUNT;

            IF affected_count <> 0 THEN
                RAISE EXCEPTION
                    'FAIL: tenant % updated tenant % row',
                    current_tenant,
                    tenant_ids[other_index];
            END IF;

            DELETE FROM organization_units
            WHERE tenant_id = tenant_ids[other_index]
              AND id IN (
                  'f1000000-0000-4000-8000-000000000001',
                  'f1000000-0000-4000-8000-000000000002',
                  'f1000000-0000-4000-8000-000000000003',
                  'f1000000-0000-4000-8000-000000000004'
              );

            GET DIAGNOSTICS affected_count = ROW_COUNT;

            IF affected_count <> 0 THEN
                RAISE EXCEPTION
                    'FAIL: tenant % deleted tenant % row',
                    current_tenant,
                    tenant_ids[other_index];
            END IF;
        END LOOP;

        RAISE NOTICE
            'PASS: tenant % sees only % and cannot modify foreign rows',
            current_tenant,
            visible_code;
    END LOOP;

    PERFORM set_config(
        'app.current_tenant_id',
        tenant_ids[1]::text,
        false
    );

    BEGIN
        INSERT INTO organization_units (
            id,
            tenant_id,
            unit_type,
            code,
            name,
            parent_id,
            party_id,
            active
        )
        VALUES (
            'f2000000-0000-4000-8000-000000000001',
            tenant_ids[2],
            'department',
            'CROSS-INSERT',
            'Cross Tenant Insert',
            NULL,
            NULL,
            true
        );

        RAISE EXCEPTION
            'FAIL: cross-tenant insert unexpectedly succeeded';
    EXCEPTION
        WHEN insufficient_privilege THEN
            RAISE NOTICE
                'PASS: cross-tenant insert rejected by RLS';
    END;

    PERFORM set_config(
        'app.current_tenant_id',
        'ffffffff-ffff-4fff-8fff-ffffffffffff',
        false
    );

    SELECT COUNT(*)
    INTO own_count
    FROM organization_units
    WHERE id IN (
        'f1000000-0000-4000-8000-000000000001',
        'f1000000-0000-4000-8000-000000000002',
        'f1000000-0000-4000-8000-000000000003',
        'f1000000-0000-4000-8000-000000000004'
    );

    IF own_count <> 0 THEN
        RAISE EXCEPTION
            'FAIL: unknown tenant context exposed % rows',
            own_count;
    END IF;

    RAISE NOTICE 'PASS: unknown tenant context exposes zero rows';
    RAISE NOTICE 'PASS: FOUR-TENANT RLS MATRIX COMPLETE';
END
$isolation$;