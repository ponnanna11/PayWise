"""
Pytest fixtures for PayWise test suite.
Configures isolated temporary SQLite databases with full seed data for each test.
"""
import os
import tempfile
import pytest
from paywise.repositories.database import init_db
from paywise.repositories.account_repo import AccountRepository
from paywise.repositories.supplier_repo import SupplierRepository
from paywise.repositories.invoice_repo import InvoiceRepository
from paywise.repositories.policy_repo import PolicyRepository
from paywise.repositories.proposal_repo import ProposalRepository
from paywise.repositories.approval_repo import ApprovalRepository
from paywise.repositories.audit_repo import AuditRepository
from paywise.services.proposal_service import ProposalService
from paywise.services.approval_service import ApprovalService
from paywise.services.revalidation_service import RevalidationService
from paywise.services.commit_service import CommitService
from paywise.services.policy_service import PolicyService
from paywise.utils.seed_data import seed_database


@pytest.fixture
def temp_db():
    """Creates a fresh, isolated SQLite database file with seed data for a test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    seed_database(db_path)

    yield db_path

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass


@pytest.fixture
def proposal_service(temp_db):
    return ProposalService(temp_db)


@pytest.fixture
def approval_service(temp_db):
    return ApprovalService(temp_db)


@pytest.fixture
def revalidation_service(temp_db):
    return RevalidationService(temp_db)


@pytest.fixture
def commit_service(temp_db):
    return CommitService(temp_db)


@pytest.fixture
def policy_service(temp_db):
    return PolicyService(temp_db)


@pytest.fixture
def account_repo(temp_db):
    return AccountRepository(temp_db)


@pytest.fixture
def invoice_repo(temp_db):
    return InvoiceRepository(temp_db)


@pytest.fixture
def policy_repo(temp_db):
    return PolicyRepository(temp_db)


@pytest.fixture
def proposal_repo(temp_db):
    return ProposalRepository(temp_db)


@pytest.fixture
def supplier_repo(temp_db):
    return SupplierRepository(temp_db)


@pytest.fixture
def approval_repo(temp_db):
    return ApprovalRepository(temp_db)


@pytest.fixture
def audit_repo(temp_db):
    return AuditRepository(temp_db)
