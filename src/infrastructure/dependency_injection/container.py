"""
Dependency injection container for managing application dependencies.

Provides centralized configuration and instantiation of domain services,
repositories, and infrastructure components with proper dependency injection.
"""

from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from src.application.services.gene_service import GeneApplicationService
    from src.application.services.variant_service import VariantApplicationService
    from src.application.services.evidence_service import EvidenceApplicationService
    from src.application.services.phenotype_service import PhenotypeApplicationService
    from src.application.services.publication_service import (
        PublicationApplicationService,
    )
    from src.application.search.search_service import UnifiedSearchService
    from src.application.export.export_service import BulkExportService
    from src.application.curation.services.detail_service import CurationDetailService

# Domain services
from src.domain.services.gene_domain_service import GeneDomainService
from src.domain.services.variant_domain_service import VariantDomainService
from src.domain.services.evidence_domain_service import EvidenceDomainService

# Domain repositories (interfaces)
from src.domain.repositories.gene_repository import GeneRepository
from src.domain.repositories.variant_repository import VariantRepository
from src.domain.repositories.phenotype_repository import PhenotypeRepository
from src.domain.repositories.evidence_repository import EvidenceRepository
from src.domain.repositories.publication_repository import PublicationRepository

# Infrastructure repositories (implementations)
from src.infrastructure.repositories.gene_repository import SqlAlchemyGeneRepository
from src.infrastructure.repositories.variant_repository import (
    SqlAlchemyVariantRepository,
)
from src.infrastructure.repositories.phenotype_repository import (
    SqlAlchemyPhenotypeRepository,
)
from src.infrastructure.repositories.evidence_repository import (
    SqlAlchemyEvidenceRepository,
)
from src.infrastructure.repositories.publication_repository import (
    SqlAlchemyPublicationRepository,
)


class DependencyContainer:
    """
    Dependency injection container for the MED13 Resource Library.

    Manages the creation and wiring of domain services, repositories,
    and infrastructure components with proper dependency injection.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize the dependency container.

        Args:
            session: SQLAlchemy database session (optional, will be created if not provided)
        """
        self._session = session

        # Initialize domain services (pure business logic)
        self._gene_domain_service = GeneDomainService()
        self._variant_domain_service = VariantDomainService()
        self._evidence_domain_service = EvidenceDomainService()

        # Initialize repository implementations
        self._gene_repository = SqlAlchemyGeneRepository(session)
        self._variant_repository = SqlAlchemyVariantRepository(session)
        self._phenotype_repository = SqlAlchemyPhenotypeRepository(session)
        self._evidence_repository = SqlAlchemyEvidenceRepository(session)
        self._publication_repository = SqlAlchemyPublicationRepository(session)

    # Domain Services (Pure Business Logic)
    @property
    def gene_domain_service(self) -> GeneDomainService:
        """Get the gene domain service."""
        return self._gene_domain_service

    @property
    def variant_domain_service(self) -> VariantDomainService:
        """Get the variant domain service."""
        return self._variant_domain_service

    @property
    def evidence_domain_service(self) -> EvidenceDomainService:
        """Get the evidence domain service."""
        return self._evidence_domain_service

    # Domain Repositories (Interfaces)
    @property
    def gene_repository(self) -> GeneRepository:
        """Get the gene repository."""
        return self._gene_repository

    @property
    def variant_repository(self) -> VariantRepository:
        """Get the variant repository."""
        return self._variant_repository

    @property
    def phenotype_repository(self) -> PhenotypeRepository:
        """Get the phenotype repository."""
        return self._phenotype_repository

    @property
    def evidence_repository(self) -> EvidenceRepository:
        """Get the evidence repository."""
        return self._evidence_repository

    @property
    def publication_repository(self) -> PublicationRepository:
        """Get the publication repository."""
        return self._publication_repository

    # Application Services (Orchestration Layer)
    def create_gene_application_service(self) -> "GeneApplicationService":
        """Create a gene application service with proper dependencies."""
        from src.application.services.gene_service import GeneApplicationService

        return GeneApplicationService(
            gene_repository=self.gene_repository,
            gene_domain_service=self.gene_domain_service,
            variant_repository=self.variant_repository,
        )

    def create_variant_application_service(self) -> "VariantApplicationService":
        """Create a variant application service with proper dependencies."""
        from src.application.services.variant_service import VariantApplicationService

        return VariantApplicationService(
            variant_repository=self.variant_repository,
            variant_domain_service=self.variant_domain_service,
            evidence_repository=self.evidence_repository,
        )

    def create_evidence_application_service(self) -> "EvidenceApplicationService":
        """Create an evidence application service with proper dependencies."""
        from src.application.services.evidence_service import EvidenceApplicationService

        return EvidenceApplicationService(
            evidence_repository=self.evidence_repository,
            evidence_domain_service=self.evidence_domain_service,
        )

    def create_phenotype_application_service(self) -> "PhenotypeApplicationService":
        """Create a phenotype application service with proper dependencies."""
        from src.application.services.phenotype_service import (
            PhenotypeApplicationService,
        )

        return PhenotypeApplicationService(
            phenotype_repository=self.phenotype_repository,
        )

    def create_publication_application_service(self) -> "PublicationApplicationService":
        """Create a publication application service with proper dependencies."""
        from src.application.services.publication_service import (
            PublicationApplicationService,
        )

        return PublicationApplicationService(
            publication_repository=self.publication_repository,
        )

    def create_unified_search_service(self) -> "UnifiedSearchService":
        """Create a unified search service with all entity services."""
        from src.application.search.search_service import UnifiedSearchService

        return UnifiedSearchService(
            gene_service=self.create_gene_application_service(),
            variant_service=self.create_variant_application_service(),
            phenotype_service=self.create_phenotype_application_service(),
            evidence_service=self.create_evidence_application_service(),
        )

    def create_bulk_export_service(self) -> "BulkExportService":
        """Create a bulk export service with all entity services."""
        from src.application.export.export_service import BulkExportService

        return BulkExportService(
            gene_service=self.create_gene_application_service(),
            variant_service=self.create_variant_application_service(),
            phenotype_service=self.create_phenotype_application_service(),
            evidence_service=self.create_evidence_application_service(),
        )

    def create_curation_detail_service(self) -> "CurationDetailService":
        """Create the curation detail service used by curator workflows."""
        from src.application.curation.conflict_detector import ConflictDetector
        from src.application.curation.services.detail_service import (
            CurationDetailService,
        )
        from src.application.curation.repositories.review_repository import (
            SqlAlchemyReviewRepository,
        )

        if self._session is None:
            raise RuntimeError(
                "Curation detail service requires an active database session"
            )

        conflict_detector = ConflictDetector(
            variant_domain_service=self.variant_domain_service,
            evidence_domain_service=self.evidence_domain_service,
        )

        return CurationDetailService(
            variant_service=self.create_variant_application_service(),
            evidence_service=self.create_evidence_application_service(),
            phenotype_repository=self.phenotype_repository,
            conflict_detector=conflict_detector,
            review_repository=SqlAlchemyReviewRepository(),
            db_session=self._session,
        )

    # Curation Services - TODO: Fix ApprovalService constructor
    # def create_curation_application_service(self) -> "ApprovalService":
    #     """Create a curation application service with proper dependencies."""
    #     # Implementation pending - ApprovalService constructor needs review
    #     pass

    # Utility methods
    def get_session(self) -> Optional[Session]:
        """Get the current database session."""
        return self._session

    def set_session(self, session: Session) -> None:
        """Set a new database session and update dependent components."""
        self._session = session

        # Update repositories with new session
        self._gene_repository = SqlAlchemyGeneRepository(session)
        self._variant_repository = SqlAlchemyVariantRepository(session)
        self._phenotype_repository = SqlAlchemyPhenotypeRepository(session)
        self._evidence_repository = SqlAlchemyEvidenceRepository(session)
        self._publication_repository = SqlAlchemyPublicationRepository(session)


__all__ = ["DependencyContainer"]
