"""
Add Pipeline Models.

Revision ID: 8f2a7b1e9d5c
Revises: 49f8a0e2c6d3
Create Date: 2025-05-20 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '8f2a7b1e9d5c'
down_revision = '49f8a0e2c6d3'
branch_labels = None
depends_on = None


def upgrade():
    # Create pipeline tables
    op.create_table(
        'pipelines',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=True),
        sa.Column('is_public', sa.Boolean(), default=False, nullable=True),
        sa.Column('version', sa.String(), default='1.0', nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_pipeline_user_id', 'pipelines', ['user_id'], unique=False)
    op.create_index('idx_pipeline_active', 'pipelines', ['is_active'], unique=False)
    op.create_index('idx_pipeline_public', 'pipelines', ['is_public'], unique=False)
    op.create_index('idx_pipeline_updated_at', 'pipelines', ['updated_at'], unique=False)
    
    op.create_table(
        'pipeline_steps',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('pipeline_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('input_mapping', sa.JSON(), nullable=True),
        sa.Column('output_mapping', sa.JSON(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), default=True, nullable=True),
        sa.Column('timeout', sa.Integer(), nullable=True),
        sa.Column('retry_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_pipeline_step_pipeline_id', 'pipeline_steps', ['pipeline_id'], unique=False)
    op.create_index('idx_pipeline_step_order', 'pipeline_steps', ['order'], unique=False)
    op.create_index('idx_pipeline_step_type', 'pipeline_steps', ['type'], unique=False)
    op.create_index('idx_pipeline_step_enabled', 'pipeline_steps', ['is_enabled'], unique=False)
    
    op.create_table(
        'pipeline_executions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('pipeline_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('input_parameters', sa.JSON(), nullable=True),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('logs', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_pipeline_execution_pipeline_id', 'pipeline_executions', ['pipeline_id'], unique=False)
    op.create_index('idx_pipeline_execution_user_id', 'pipeline_executions', ['user_id'], unique=False)
    op.create_index('idx_pipeline_execution_status', 'pipeline_executions', ['status'], unique=False)
    op.create_index('idx_pipeline_execution_started_at', 'pipeline_executions', ['started_at'], unique=False)
    
    op.create_table(
        'pipeline_step_executions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('pipeline_execution_id', sa.String(), nullable=False),
        sa.Column('step_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('inputs', sa.JSON(), nullable=True),
        sa.Column('outputs', sa.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('logs', sa.JSON(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('model_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['model_id'], ['models.id'], ),
        sa.ForeignKeyConstraint(['pipeline_execution_id'], ['pipeline_executions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['step_id'], ['pipeline_steps.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_step_execution_pipeline_execution_id', 'pipeline_step_executions', ['pipeline_execution_id'], unique=False)
    op.create_index('idx_step_execution_step_id', 'pipeline_step_executions', ['step_id'], unique=False)
    op.create_index('idx_step_execution_status', 'pipeline_step_executions', ['status'], unique=False)
    op.create_index('idx_step_execution_started_at', 'pipeline_step_executions', ['started_at'], unique=False)


def downgrade():
    # Drop pipeline tables
    op.drop_table('pipeline_step_executions')
    op.drop_table('pipeline_executions')
    op.drop_table('pipeline_steps')
    op.drop_table('pipelines')