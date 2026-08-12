"""Add email verification

Revision ID: 3bed19a2df77
Revises: b447817e048a
Create Date: 2026-08-12 12:48:00.096822

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3bed19a2df77'
down_revision = 'b447817e048a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('email_verification_tokens',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('token_hash', sa.String(length=255), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('email_verification_tokens', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_email_verification_tokens_token_hash'), ['token_hash'], unique=True)
        batch_op.create_index(batch_op.f('ix_email_verification_tokens_user_id'), ['user_id'], unique=False)

    # Manually added server_default: autogenerate captured the
    # Python-side model default (False) but NOT a server-side
    # default -- without one, adding a NOT NULL column to a table
    # that already has real rows (existing registered users) makes
    # Postgres reject the ALTER TABLE outright, since it has no value
    # to backfill those rows with. Existing users are correctly
    # treated as unverified (false) until they go through the flow.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'email_verified',
                sa.Boolean(),
                server_default=sa.text('false'),
                nullable=False,
            )
        )


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('email_verified')

    with op.batch_alter_table('email_verification_tokens', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_email_verification_tokens_user_id'))
        batch_op.drop_index(batch_op.f('ix_email_verification_tokens_token_hash'))
    op.drop_table('email_verification_tokens')
