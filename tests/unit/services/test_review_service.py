from src.application.curation.repositories.review_repository import (
    SqlAlchemyReviewRepository,
)
from src.application.curation.services.review_service import ReviewService, ReviewQuery
from src.database.session import SessionLocal, engine
from src.models.database.base import Base


def setup_module(module):
    # Create tables once for this test module
    Base.metadata.create_all(engine)


def test_review_service_submit_and_list():
    repo = SqlAlchemyReviewRepository()
    service = ReviewService(repo)

    with SessionLocal() as db:  # type: Session
        created = service.submit(
            db, entity_type="genes", entity_id="GENE2", priority="low"
        )
        assert created.id is not None

        items = service.list_queue(
            db, ReviewQuery(entity_type="genes", status="pending")
        )
        assert any(it.id == created.id for it in items)
