"""add location table and location_id column to activities

Revision ID: 2e036fe7c54d
Revises: 
Create Date: 2025-04-15 14:23:26.172117

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e036fe7c54d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the locations table
    op.create_table(
        'locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Add the location_id column to the activities table
    op.add_column('activities', sa.Column('location_id', sa.Integer(), nullable=True))

    # Add foreign key constraint to activities table
    op.create_foreign_key(
        'fk_activities_location_id', 'activities', 'locations', ['location_id'], ['id']
    )

def downgrade() -> None:
    # Drop the foreign key constraint first
    op.drop_constraint('fk_activities_location_id', 'activities', type_='foreignkey')

    # Drop the location_id column
    op.drop_column('activities', 'location_id')

    # Drop the locations table
    op.drop_table('locations')
