"""Seed standard units of measure (required reference data).

products.base_uom has a foreign key to units_of_measure(code), but a database
built from the migration chain had no units of measure and no API creates them,
so no product could be created on a fresh install.

Revision ID: ff_seed_uom_001
Revises: ff_phaseb_rls_001
"""

from alembic import op

revision = "ff_seed_uom_001"
down_revision = "ff_phaseb_rls_001"
branch_labels = None
depends_on = None

UNITS: tuple[tuple[str, str, int], ...] = (
    ("EA", "Each", 0),
    ("PK", "Pack", 0),
    ("BOX", "Box", 0),
    ("CS", "Case", 0),
    ("SET", "Set", 0),
    ("PAL", "Pallet", 0),
    ("HR", "Hour", 2),
    ("DAY", "Day", 2),
    ("KG", "Kilogram", 3),
    ("G", "Gram", 3),
    ("LB", "Pound", 3),
    ("OZ", "Ounce", 3),
    ("L", "Litre", 3),
    ("ML", "Millilitre", 3),
    ("GAL", "Gallon", 3),
    ("M", "Metre", 3),
    ("CM", "Centimetre", 2),
    ("FT", "Foot", 2),
    ("IN", "Inch", 2),
)


def upgrade() -> None:
    values = ", ".join(f"('{code}', '{name}', {precision})" for code, name, precision in UNITS)
    op.execute(
        "INSERT INTO units_of_measure (code, name, precision) "
        f"VALUES {values} ON CONFLICT (code) DO NOTHING"
    )


def downgrade() -> None:
    # Reference data is intentionally retained: products may reference these
    # codes, and removing them would break existing records.
    pass
