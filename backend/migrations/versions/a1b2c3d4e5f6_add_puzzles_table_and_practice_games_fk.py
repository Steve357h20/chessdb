"""add puzzles table and practice_games foreign key

Revision ID: a1b2c3d4e5f6
Revises: 4c0f851ac9b1
Create Date: 2026-05-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = '4c0f851ac9b1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('puzzles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('difficulty', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('hint', sa.Text(), nullable=True),
        sa.Column('fen', sa.Text(), nullable=False),
        sa.Column('source_game_id', sa.Integer(), nullable=True),
        sa.Column('from_move', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('is_preset', sa.Boolean(), nullable=True),
        sa.Column('practice_count', sa.Integer(), nullable=True),
        sa.Column('solve_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('puzzles', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_puzzles_source_game_id'), ['source_game_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_puzzles_created_by'), ['created_by'], unique=False)
        batch_op.create_index(batch_op.f('ix_puzzles_is_preset'), ['is_preset'], unique=False)

    with op.batch_alter_table('practice_games', schema=None) as batch_op:
        batch_op.alter_column('puzzle_id',
               existing_type=sa.String(length=50),
               type_=sa.Integer(),
               existing_nullable=True)
        batch_op.create_foreign_key(batch_op.f('fk_practice_games_puzzle_id_puzzles'), 'puzzles', ['puzzle_id'], ['id'])
        batch_op.create_index(batch_op.f('ix_practice_games_puzzle_id'), ['puzzle_id'], unique=False)


def downgrade():
    with op.batch_alter_table('practice_games', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_practice_games_puzzle_id'))
        batch_op.drop_constraint(batch_op.f('fk_practice_games_puzzle_id_puzzles'), type_='foreignkey')
        batch_op.alter_column('puzzle_id',
               existing_type=sa.Integer(),
               type_=sa.String(length=50),
               existing_nullable=True)

    with op.batch_alter_table('puzzles', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_puzzles_is_preset'))
        batch_op.drop_index(batch_op.f('ix_puzzles_created_by'))
        batch_op.drop_index(batch_op.f('ix_puzzles_source_game_id'))

    op.drop_table('puzzles')
