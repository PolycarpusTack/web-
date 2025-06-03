"""create_workspace_invitations

Revision ID: f1b2c3d4e5f6
Revises: d063694a8a45
Create Date: 2025-06-02 14:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1b2c3d4e5f6'
down_revision = 'd063694a8a45'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create workspace_invitations table
    op.create_table('workspace_invitations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('workspace_id', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('token', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invited_by', sa.String(), nullable=True),
        sa.Column('accepted_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['accepted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspace_invitations_email'), 'workspace_invitations', ['email'], unique=False)
    op.create_index(op.f('ix_workspace_invitations_token'), 'workspace_invitations', ['token'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_workspace_invitations_token'), table_name='workspace_invitations')
    op.drop_index(op.f('ix_workspace_invitations_email'), table_name='workspace_invitations')
    op.drop_table('workspace_invitations')