"""add github config to user settings

Revision ID: a1b2c3d4e5f6
Revises: f1b2c3d4e5f6
Create Date: 2025-01-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add github_config column to user_settings table
    op.add_column('user_settings', sa.Column('github_config', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove github_config column from user_settings table
    op.drop_column('user_settings', 'github_config')