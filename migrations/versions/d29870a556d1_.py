"""empty message

Revision ID: d29870a556d1
Revises: 75b1b7f9bfb3
Create Date: 2019-10-01 13:20:55.097338

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd29870a556d1'
down_revision = '75b1b7f9bfb3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('placename', schema=None) as batch_op:
        batch_op.drop_column('description')

    with op.batch_alter_table('placename_role', schema=None) as batch_op:
        batch_op.add_column(sa.Column('description', sa.String(length=100), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('placename_role', schema=None) as batch_op:
        batch_op.drop_column('description')

    with op.batch_alter_table('placename', schema=None) as batch_op:
        batch_op.add_column(sa.Column('description', sa.VARCHAR(), nullable=True))

    # ### end Alembic commands ###