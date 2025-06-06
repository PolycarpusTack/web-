"""add_workspace_invitations_table

Revision ID: d063694a8a45
Revises: e13941c35c2d
Create Date: 2025-06-02 14:02:52.481379

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd063694a8a45'
down_revision = 'e13941c35c2d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, 'conversations', 'workspaces', ['workspace_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'conversations', type_='foreignkey')
    # ### end Alembic commands ###
