Deep Compliance Findings (Still Pending)

  - Type definitions centralization: many TypedDict definitions live outside
    src/type_definitions/, e.g. src/routes/search.py, src/application/services/
    authorization_service.py, src/application/packaging/packaging_types.py,
    src/domain/transform/parsers/clinvar_parser.py, src/infrastructure/
    repositories/gene_repository.py, src/database/seed_data.py.
  - Frontend orchestration: several flows still rely on client-side queries/
    mutations rather than server actions, e.g. src/web/components/research-
    spaces/ResearchSpaceDetail.tsx, src/web/lib/queries/research-spaces.ts,
    src/web/lib/api/research-spaces.ts, src/web/app/(dashboard)/spaces/
    [spaceId]/page.tsx.
