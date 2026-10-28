"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-26 16:00:00.000000

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
    # 1. Institutions
    op.create_table(
        'institutions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('aicte_id', sa.String(length=50), nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('region', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False, server_default='Govt'),
        sa.Column('trust_score', sa.Float(), nullable=False, server_default='95.0'),
        sa.Column('approved_intake', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('actual_enrolment', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('supernumerary_intake', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_institutions_aicte_id'), 'institutions', ['aicte_id'], unique=True)
    op.create_index(op.f('ix_institutions_name'), 'institutions', ['name'], unique=False)
    op.create_index(op.f('ix_institutions_state'), 'institutions', ['state'], unique=False)
    op.create_index(op.f('ix_institutions_region'), 'institutions', ['region'], unique=False)

    # 2. Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('institution_id', sa.String(length=36), sa.ForeignKey('institutions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('mfa_secret', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)

    # 3. Program Branches
    op.create_table(
        'program_branches',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('institution_id', sa.String(length=36), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('program', sa.String(length=50), nullable=False),
        sa.Column('branch', sa.String(length=150), nullable=False),
        sa.Column('academic_year', sa.String(length=20), nullable=False, server_default='2025-2026'),
        sa.Column('approved_intake', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('enrolled_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('supernumerary_intake', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index(op.f('ix_program_branches_institution_id'), 'program_branches', ['institution_id'], unique=False)

    # 4. Students
    op.create_table(
        'students',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('apaar_id', sa.String(length=12), nullable=False),
        sa.Column('institution_id', sa.String(length=36), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('program_branch_id', sa.String(length=36), sa.ForeignKey('program_branches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name_encrypted', sa.Text(), nullable=False),
        sa.Column('dob_encrypted', sa.Text(), nullable=False),
        sa.Column('gender', sa.String(length=20), nullable=False),
        sa.Column('program', sa.String(length=50), nullable=False),
        sa.Column('branch', sa.String(length=150), nullable=False),
        sa.Column('year_of_study', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('admission_date', sa.Date(), nullable=False),
        sa.Column('quota_type', sa.String(length=50), nullable=False, server_default='Merit'),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='General'),
        sa.Column('is_supernumerary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_nri', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_oci', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_foreign_national', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('document_hash', sa.String(length=64), nullable=False),
        sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='VALIDATED'),
        sa.Column('cached_name', sa.String(length=255), nullable=True),
        sa.Column('cached_dob', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_students_apaar_id'), 'students', ['apaar_id'], unique=False)
    op.create_index(op.f('ix_students_institution_id'), 'students', ['institution_id'], unique=False)

    # 5. Upload Batches
    op.create_table(
        'upload_batches',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('institution_id', sa.String(length=36), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('total_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('valid_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('flagged_records', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('uploaded_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('error_summary', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 6. Validation Flags
    op.create_table(
        'validation_flags',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('upload_batch_id', sa.String(length=36), sa.ForeignKey('upload_batches.id', ondelete='CASCADE'), nullable=True),
        sa.Column('student_id', sa.String(length=36), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=True),
        sa.Column('institution_id', sa.String(length=36), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('apaar_id', sa.String(length=12), nullable=True),
        sa.Column('rule_code', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='HIGH'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('fix_suggestion', sa.Text(), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolved_by', sa.String(length=100), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_validation_flags_apaar_id'), 'validation_flags', ['apaar_id'], unique=False)
    op.create_index(op.f('ix_validation_flags_rule_code'), 'validation_flags', ['rule_code'], unique=False)

    # 7. Cases
    op.create_table(
        'cases',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('case_number', sa.String(length=50), nullable=False, unique=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('institution_id', sa.String(length=36), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('clash_institution_id', sa.String(length=36), sa.ForeignKey('institutions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('related_student_apaar', sa.String(length=12), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='OPEN'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='HIGH'),
        sa.Column('sla_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('opened_by_type', sa.String(length=50), nullable=False, server_default='SENTINEL'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('action_draft', sa.Text(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('evidence_pack', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_cases_case_number'), 'cases', ['case_number'], unique=True)

    # 8. Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('sequence_number', sa.BigInteger(), nullable=False, unique=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.String(length=50), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('ip_address', sa.String(length=50), nullable=False, server_default='127.0.0.1'),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('payload_hash', sa.String(length=64), nullable=False),
        sa.Column('previous_hash', sa.String(length=64), nullable=False),
        sa.Column('current_hash', sa.String(length=64), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
    )
    op.create_index(op.f('ix_audit_logs_sequence_number'), 'audit_logs', ['sequence_number'], unique=True)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)

    # 9. Consent Wallets
    op.create_table(
        'consent_wallets',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('student_apaar_id', sa.String(length=12), nullable=False),
        sa.Column('verifier_type', sa.String(length=50), nullable=False),
        sa.Column('allowed_fields', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('otp_code', sa.String(length=6), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_consent_wallets_student_apaar_id'), 'consent_wallets', ['student_apaar_id'], unique=False)

    # 10. Verification Access Logs
    op.create_table(
        'verification_access_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('student_apaar_id', sa.String(length=12), nullable=False),
        sa.Column('verifier_name', sa.String(length=150), nullable=False),
        sa.Column('verifier_org', sa.String(length=150), nullable=False),
        sa.Column('verifier_role', sa.String(length=50), nullable=False, server_default='EMPLOYER_VERIFIER'),
        sa.Column('accessed_fields', sa.JSON(), nullable=False),
        sa.Column('purpose', sa.String(length=255), nullable=False, server_default='Employment Verification'),
        sa.Column('ip_address', sa.String(length=50), nullable=False, server_default='127.0.0.1'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_verification_access_logs_student_apaar_id'), 'verification_access_logs', ['student_apaar_id'], unique=False)

    # 11. Institution Trust History
    op.create_table(
        'institution_trust_history',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('institution_id', sa.String(length=36), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('data_quality_factor', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('timeliness_factor', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('anomaly_penalty', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('resolution_speed_factor', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('institution_trust_history')
    op.drop_table('verification_access_logs')
    op.drop_table('consent_wallets')
    op.drop_table('audit_logs')
    op.drop_table('cases')
    op.drop_table('validation_flags')
    op.drop_table('upload_batches')
    op.drop_table('students')
    op.drop_table('program_branches')
    op.drop_table('users')
    op.drop_table('institutions')
