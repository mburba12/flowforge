\set ON_ERROR_STOP on

BEGIN;

DELETE FROM organization_units
WHERE id IN (
    'f1000000-0000-4000-8000-000000000001',
    'f1000000-0000-4000-8000-000000000002',
    'f1000000-0000-4000-8000-000000000003',
    'f1000000-0000-4000-8000-000000000004',
    'f2000000-0000-4000-8000-000000000001'
);

DELETE FROM tenants
WHERE id IN (
    'f0000000-0000-4000-8000-000000000001',
    'f0000000-0000-4000-8000-000000000002',
    'f0000000-0000-4000-8000-000000000003',
    'f0000000-0000-4000-8000-000000000004'
);

INSERT INTO tenants (
    id,
    name,
    slug,
    status,
    is_deleted
)
VALUES
    (
        'f0000000-0000-4000-8000-000000000001',
        'Live Acceptance Tenant Alpha',
        'live-acceptance-alpha',
        'active',
        false
    ),
    (
        'f0000000-0000-4000-8000-000000000002',
        'Live Acceptance Tenant Bravo',
        'live-acceptance-bravo',
        'active',
        false
    ),
    (
        'f0000000-0000-4000-8000-000000000003',
        'Live Acceptance Tenant Charlie',
        'live-acceptance-charlie',
        'active',
        false
    ),
    (
        'f0000000-0000-4000-8000-000000000004',
        'Live Acceptance Tenant Delta',
        'live-acceptance-delta',
        'active',
        false
    );

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
VALUES
    (
        'f1000000-0000-4000-8000-000000000001',
        'f0000000-0000-4000-8000-000000000001',
        'department',
        'ALPHA-ONLY',
        'Alpha Private Unit',
        NULL,
        NULL,
        true
    ),
    (
        'f1000000-0000-4000-8000-000000000002',
        'f0000000-0000-4000-8000-000000000002',
        'department',
        'BRAVO-ONLY',
        'Bravo Private Unit',
        NULL,
        NULL,
        true
    ),
    (
        'f1000000-0000-4000-8000-000000000003',
        'f0000000-0000-4000-8000-000000000003',
        'department',
        'CHARLIE-ONLY',
        'Charlie Private Unit',
        NULL,
        NULL,
        true
    ),
    (
        'f1000000-0000-4000-8000-000000000004',
        'f0000000-0000-4000-8000-000000000004',
        'department',
        'DELTA-ONLY',
        'Delta Private Unit',
        NULL,
        NULL,
        true
    );

COMMIT;
