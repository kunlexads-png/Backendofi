"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-04 05:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Arrivals table
    op.create_table(
        'arrivals',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('arrival_id', sa.String(length=50), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('time', sa.String(length=10), nullable=False),
        sa.Column('truck_number', sa.String(length=50), nullable=False),
        sa.Column('driver_name', sa.String(length=100), nullable=False),
        sa.Column('supplier', sa.String(length=150), nullable=False),
        sa.Column('customer', sa.String(length=150), nullable=True),
        sa.Column('product', sa.String(length=100), nullable=False),
        sa.Column('number_of_bags', sa.Integer(), nullable=False),
        sa.Column('gross_weight', sa.Float(), nullable=False),
        sa.Column('tare_weight', sa.Float(), nullable=False),
        sa.Column('net_weight', sa.Float(), nullable=False),
        sa.Column('batch_number', sa.String(length=50), nullable=False),
        sa.Column('warehouse', sa.String(length=100), nullable=False),
        sa.Column('cluster', sa.String(length=100), nullable=False),
        sa.Column('moisture', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('offloading_status', sa.String(length=50), nullable=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_arrivals_arrival_id'), 'arrivals', ['arrival_id'], unique=True)
    op.create_index(op.f('ix_arrivals_date'), 'arrivals', ['date'], unique=False)
    op.create_index(op.f('ix_arrivals_truck_number'), 'arrivals', ['truck_number'], unique=False)
    op.create_index(op.f('ix_arrivals_supplier'), 'arrivals', ['supplier'], unique=False)
    op.create_index(op.f('ix_arrivals_batch_number'), 'arrivals', ['batch_number'], unique=False)
    op.create_index(op.f('ix_arrivals_status'), 'arrivals', ['status'], unique=False)

    # Finished Goods table
    op.create_table(
        'finished_goods',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('record_id', sa.String(length=50), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('product', sa.String(length=100), nullable=False),
        sa.Column('product_type', sa.String(length=100), nullable=False),
        sa.Column('batch_number', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('number_of_bags', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('warehouse_location', sa.String(length=100), nullable=False),
        sa.Column('customer', sa.String(length=150), nullable=True),
        sa.Column('production_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('sap_batch', sa.String(length=50), nullable=True),
        sa.Column('storage_location', sa.String(length=100), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_finished_goods_record_id'), 'finished_goods', ['record_id'], unique=True)
    op.create_index(op.f('ix_finished_goods_date'), 'finished_goods', ['date'], unique=False)
    op.create_index(op.f('ix_finished_goods_product'), 'finished_goods', ['product'], unique=False)
    op.create_index(op.f('ix_finished_goods_batch_number'), 'finished_goods', ['batch_number'], unique=False)
    op.create_index(op.f('ix_finished_goods_status'), 'finished_goods', ['status'], unique=False)

    # By-products table
    op.create_table(
        'byproducts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('record_id', sa.String(length=50), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('product', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('batch_number', sa.String(length=50), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('sap_batch', sa.String(length=50), nullable=True),
        sa.Column('customer', sa.String(length=150), nullable=True),
        sa.Column('warehouse_location', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_byproducts_record_id'), 'byproducts', ['record_id'], unique=True)
    op.create_index(op.f('ix_byproducts_date'), 'byproducts', ['date'], unique=False)
    op.create_index(op.f('ix_byproducts_product'), 'byproducts', ['product'], unique=False)
    op.create_index(op.f('ix_byproducts_batch_number'), 'byproducts', ['batch_number'], unique=False)

    # Stock movements table
    op.create_table(
        'stock_movements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=50), nullable=False),
        sa.Column('product', sa.String(length=100), nullable=False),
        sa.Column('module', sa.String(length=50), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False, server_default=sa.text('0')),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('batch', sa.String(length=50), nullable=False),
        sa.Column('reference_number', sa.String(length=100), nullable=False),
        sa.Column('previous_balance', sa.Float(), nullable=False),
        sa.Column('new_balance', sa.Float(), nullable=False),
        sa.Column('user', sa.String(length=100), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stock_movements_transaction_id'), 'stock_movements', ['transaction_id'], unique=True)
    op.create_index(op.f('ix_stock_movements_product'), 'stock_movements', ['product'], unique=False)
    op.create_index(op.f('ix_stock_movements_module'), 'stock_movements', ['module'], unique=False)
    op.create_index(op.f('ix_stock_movements_transaction_type'), 'stock_movements', ['transaction_type'], unique=False)
    op.create_index(op.f('ix_stock_movements_batch'), 'stock_movements', ['batch'], unique=False)
    op.create_index(op.f('ix_stock_movements_reference_number'), 'stock_movements', ['reference_number'], unique=False)

    # Uploaded files table
    op.create_table(
        'uploaded_files',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=20), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('extracted_data', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('uploaded_files')
    op.drop_table('stock_movements')
    op.drop_table('byproducts')
    op.drop_table('finished_goods')
    op.drop_table('arrivals')
    op.drop_table('users')
