"""initial schema

Revision ID: 20260413_0001
Revises: 
Create Date: 2026-04-13

"""

from alembic import op
import sqlalchemy as sa


revision = "20260413_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("preferences", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "itineraries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("destination", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("start_date", sa.String(length=30), nullable=False),
        sa.Column("end_date", sa.String(length=30), nullable=False),
        sa.Column("total_estimated_cost", sa.Float(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("decision_trace", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_itineraries_user_id", "itineraries", ["user_id"])
    op.create_index("ix_itineraries_destination", "itineraries", ["destination"])

    op.create_table(
        "bookings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("itinerary_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("booking_type", sa.String(length=50), nullable=False),
        sa.Column("provider", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("external_reference", sa.String(length=255), nullable=False),
        sa.Column("request_payload", sa.JSON(), nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["itinerary_id"], ["itineraries.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_bookings_itinerary_id", "bookings", ["itinerary_id"])
    op.create_index("ix_bookings_user_id", "bookings", ["user_id"])

    op.create_table(
        "context_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("destination", sa.String(length=255), nullable=False),
        sa.Column("signal_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "disruption_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("itinerary_id", sa.String(length=36), nullable=False),
        sa.Column("destination", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("impact_score", sa.String(length=20), nullable=False),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "explanation_traces",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("itinerary_id", sa.String(length=36), nullable=False),
        sa.Column("stage", sa.String(length=80), nullable=False),
        sa.Column("trace_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["itinerary_id"], ["itineraries.id"]),
    )

    op.create_table(
        "feedback",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("itinerary_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("comment", sa.String(length=1024), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["itinerary_id"], ["itineraries.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )


def downgrade() -> None:
    op.drop_table("feedback")
    op.drop_table("explanation_traces")
    op.drop_table("disruption_events")
    op.drop_table("context_snapshots")
    op.drop_index("ix_bookings_user_id", table_name="bookings")
    op.drop_index("ix_bookings_itinerary_id", table_name="bookings")
    op.drop_table("bookings")
    op.drop_index("ix_itineraries_destination", table_name="itineraries")
    op.drop_index("ix_itineraries_user_id", table_name="itineraries")
    op.drop_table("itineraries")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
