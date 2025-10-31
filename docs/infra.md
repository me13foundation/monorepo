# MED13 Resource Library - Infrastructure Guide

## Overview

This document outlines the infrastructure setup for the MED13 Resource Library (Phase 0), a Python-based application deployed on Google Cloud Platform using Cloud Run for serverless deployment with automated CI/CD via GitHub Actions.

## Architecture Decisions

### Deployment Platform: Google Cloud Run (Source Deployments)
**Decision**: Use Cloud Run with source deployments instead of Docker containers
**Rationale**:
- Operational simplicity prioritized over Docker complexity
- Intermediate Docker experience - source deployments reduce maintenance overhead
- Google handles containerization automatically
- Faster development cycle and easier debugging
- Sufficient for Python application with standard dependencies

### CI/CD Pipeline: GitHub Actions
**Decision**: Automated deployments triggered by GitHub pushes
**Rationale**:
- Native GitHub integration with existing repository
- Cost-effective (GitHub Actions free tier sufficient)
- Familiar YAML-based configuration
- Automatic testing and deployment on main branch pushes

### Database: SQLite (Development) / Cloud SQL PostgreSQL (Production)
**Decision**: SQLite for local development, Cloud SQL PostgreSQL for production
**Rationale**:
- Cost-efficient and fully compatible with Python ecosystem
- Managed service reduces operational overhead
- Automatic backups, scaling, and security patches
- JSONB support for flexible metadata storage as specified in requirements
- Private IP connectivity with Cloud Run for security

### Secrets Management: Google Cloud Secret Manager
**Decision**: Centralized secrets management
**Rationale**:
- Secure, audited, and encrypted storage
- Native Cloud Run integration via IAM
- Automatic versioning and rotation capabilities
- Cost-effective at $0.06 per secret per month
- Eliminates credential exposure in code or environment variables

## Infrastructure Components

### Application Stack
- **Runtime**: Python 3.11
- **Framework**: FastAPI (REST/GraphQL API)
- **UI**: Plotly Dash for curation interface
- **Database**: SQLite (development) / PostgreSQL 15+ with JSONB (production)
- **Deployment**: Cloud Run (serverless with source deployments)
- **Containerization**: Dockerfile for local development

### Google Cloud Services
- **Cloud Run**: Serverless application hosting
- **Cloud SQL**: Managed PostgreSQL database
- **Secret Manager**: Secure secrets storage
- **Cloud Build**: (Optional) For complex build processes
- **Cloud Storage**: (Future) For data exports and backups

## Repository Structure

```
.github/
  workflows/
    deploy.yml              # GitHub Actions CI/CD pipeline
Dockerfile                   # Local development and future containerization
Makefile                     # Development workflow automation
pyproject.toml               # Modern Python packaging and tool configuration
requirements.txt             # Production Python dependencies (auto-generated)
requirements-dev.txt         # Development dependencies
Procfile                     # Cloud Run source deployment config
README.md                    # Project documentation
docs/
  infra.md                   # This infrastructure guide
scripts/                     # Utility scripts
src/                         # Application source code
  main.py                    # FastAPI application entry point
  models/                    # Pydantic models with strict typing
  routes/                    # API endpoints with type hints
  services/                  # Business logic with comprehensive validation
  database/                  # Database connection and queries with typing
tests/                       # Comprehensive test suite
migrations/                  # Database migration scripts
```

## Local Development Setup

### Dockerfile
Maintain a working Dockerfile for local development and future containerization:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### CORS Configuration
Configure CORS in FastAPI for frontend integration:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://med13foundation.org",
        "https://curate.med13foundation.org",
        "http://localhost:3000",  # For local development
        "http://localhost:8080"   # For local development
    ],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True,
)

### Makefile for Development Workflow
Use the provided Makefile to automate common development tasks:

```bash
# Get help with available commands
make help

# Set up development environment
make setup-dev

# Install dependencies
make install-dev

# Run tests
make test

# Run application locally
make run-local

# Run full CI pipeline locally
make ci

# Deploy to staging
make deploy-staging

# Clean up temporary files
make clean
```

## Code Quality & Type Safety

### Robust Tooling Stack

The project implements a comprehensive quality assurance pipeline with multiple layers of validation:

#### **Type Safety & Validation**
- **Pydantic v2**: Data validation with strict typing and JSON schema generation
- **MyPy**: Static type checking with strict settings (--strict, --show-error-codes)
- **Type Hints**: Comprehensive type annotations throughout the codebase

#### **Code Quality Tools**
- **Black**: Code formatting with 88-character line length
- **Ruff**: Fast Python linter and import sorter (replaces flake8 + isort)
- **Flake8**: Additional style and error checking
- **Pre-commit Hooks**: Automated quality checks before commits

#### **Security Scanning**
- **Bandit**: Security vulnerability scanner for Python code
- **Safety**: Dependency vulnerability checker
- **Pip-audit**: Comprehensive package vulnerability assessment

#### **Testing & Coverage**
- **Pytest**: Comprehensive test framework with async support
- **Coverage.py**: Code coverage reporting (>90% target)
- **Pytest-xdist**: Parallel test execution
- **Pytest-watch**: Auto-run tests during development

### Type Safety Implementation

#### **Pydantic Models**
```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class Gene(BaseModel):
    gene_id: str = Field(..., min_length=1, max_length=50)
    symbol: str = Field(..., pattern=r'^[A-Z0-9]+$')
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper()

class Variant(BaseModel):
    variant_id: str
    gene_id: str
    hgvs: str
    clinvar_id: Optional[str] = None
    phenotypes: List[Phenotype] = Field(default_factory=list)
```

#### **FastAPI with Type Hints**
```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Annotated

app = FastAPI(title="MED13 Resource Library", version="0.1.0")

@app.get("/api/variants/", response_model=List[VariantResponse])
async def get_variants(
    skip: int = 0,
    limit: int = 100,
    gene_symbol: Optional[str] = None,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> List[VariantResponse]:
    """Get variants with optional filtering."""
    # Implementation with full type safety
    pass

@app.post("/api/variants/", response_model=VariantResponse, status_code=201)
async def create_variant(
    variant: VariantCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> VariantResponse:
    """Create a new variant with validation."""
    # Full type safety and validation
    pass
```

### Quality Assurance Pipeline

#### **Pre-commit Configuration**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.14
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## CI/CD Pipeline

### GitHub Actions Workflow (`.github/workflows/deploy.yml`)

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  release:
    types: [ published ]

env:
  REGION: us-central1
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run code quality checks
      run: |
        echo "Running Black formatting check..."
        black --check src tests
        echo "Running Ruff linting..."
        ruff check src tests
        echo "Running flake8..."
        flake8 src tests --max-line-length=88 --extend-ignore=E203,W503

    - name: Run type checking
      run: mypy src --strict --show-error-codes

    - name: Run security audit
      run: |
        echo "Running pip-audit..."
        pip-audit --format json | tee pip-audit-results.json || true
        echo "Running safety..."
        safety check --output json | tee safety-results.json || true
        echo "Running bandit..."
        bandit -r src -f json -o bandit-results.json || true

    - name: Upload quality check results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: quality-check-results
        path: |
          pip-audit-results.json
          safety-results.json
          bandit-results.json

    - name: Run tests with coverage
      run: pytest --cov=src --cov-report=xml --cov-report=term-missing

    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  deploy-staging:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request' && github.event.action == 'closed' && github.event.pull_request.merged == true
    environment: staging
    steps:
    - uses: actions/checkout@v4

    - name: Authenticate to Google Cloud
      uses: google-github-actions/auth@v2
      with:
        credentials_json: ${{ secrets.GCP_SA_KEY_STAGING }}

    - name: Deploy to Cloud Run (Staging)
      uses: google-github-actions/deploy-cloudrun@v2
      with:
        service: med13-resource-library-staging
        source: .
        region: ${{ env.REGION }}
        allow-unauthenticated: false

  deploy-production:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'release' && github.event.action == 'published'
    environment: production
    steps:
    - uses: actions/checkout@v4

    - name: Authenticate to Google Cloud
      uses: google-github-actions/auth@v2
      with:
        credentials_json: ${{ secrets.GCP_SA_KEY_PROD }}

    - name: Deploy to Cloud Run (Production)
      uses: google-github-actions/deploy-cloudrun@v2
      with:
        service: med13-resource-library
        source: .
        region: ${{ env.REGION }}
        allow-unauthenticated: false

    - name: Deploy Curation UI
      uses: google-github-actions/deploy-cloudrun@v2
      with:
        service: med13-curation
        source: .
        region: ${{ env.REGION }}
        allow-unauthenticated: false
```

### Deployment Configuration

#### Procfile (Required for source deployments)
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### requirements.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0
pytest==7.4.3
google-cloud-secretmanager==2.16.3
plotly==5.17.0
dash==2.14.0
httpx==0.25.2
python-multipart==0.0.6
```

## Database Configuration

### Local Development (SQLite)
- **Database**: SQLite file-based database (`med13.db`)
- **Setup**: Automatic file creation, zero configuration
- **Migration**: Alembic handles schema changes
- **Data**: Persisted locally, easy to reset for development

### Production (Cloud SQL)
- **Instance Type**: PostgreSQL 15
- **Machine Type**: db-f1-micro (for development) or db-g1-small (for production)
- **Storage**: 10GB SSD (autoscale enabled)
- **Backup**: Daily backups with 7-day retention
- **High Availability**: Single zone (upgrade to regional for production)

### Connection Security
- **Private IP**: Enabled for Cloud Run connectivity
- **IAM Authentication**: Service account-based access
- **SSL**: Required for all connections
- **VPC Network**: Default network with private services access

## Secrets Management

### Required Secrets
- `med13-db-password`: Database password
- `med13-db-user`: Database username
- `clinvar-api-key`: ClinVar API access token
- `pubmed-api-key`: PubMed API key
- `crossref-api-key`: Crossref API token
- `omim-api-key`: OMIM API key
- `oauth-client-secret`: OAuth2 client secret
- `jwt-secret-key`: JWT signing secret

### Service Account Setup (Per Environment)
Create separate service accounts for development, staging, and production environments:

```bash
# Create environment-specific service accounts
gcloud iam service-accounts create med13-dev \
  --description="MED13 Development environment"

gcloud iam service-accounts create med13-staging \
  --description="MED13 Staging environment"

gcloud iam service-accounts create med13-prod \
  --description="MED13 Production environment"

# Grant necessary permissions to each service account
for env in dev staging prod; do
  SA="med13-${env}@YOUR_PROJECT.iam.gserviceaccount.com"

  # Secret Manager access
  gcloud projects add-iam-policy-binding YOUR_PROJECT \
    --member="serviceAccount:$SA" \
    --role="roles/secretmanager.secretAccessor"

  # Cloud SQL client access
  gcloud projects add-iam-policy-binding YOUR_PROJECT \
    --member="serviceAccount:$SA" \
    --role="roles/cloudsql.client"

  # Cloud Run invoker (for production service account)
  if [ "$env" = "prod" ]; then
    gcloud projects add-iam-policy-binding YOUR_PROJECT \
      --member="serviceAccount:$SA" \
      --role="roles/run.invoker"
  fi
done
```

Each GitHub environment stores its own `GCP_SA_KEY` secret for secure authentication.

## Security Configuration

### Authentication & Authorization
- **Backend Authentication**: Required for curation interface
- **OAuth2 Integration**: Google Cloud Identity Platform
- **JWT Tokens**: For API authentication
- **Role-Based Access**: Public read, curator write access
- **Service Separation**: Separate Cloud Run services for public API and curation UI

### Network Security
- **HTTPS Only**: Cloud Run enforces SSL
- **Private Database**: Cloud SQL accessible only via private IP
- **VPC Service Controls**: (Optional) For additional isolation
- **Firewall Rules**: Restrictive ingress rules

## Cost Optimization

### Estimated Monthly Costs
- **Cloud Run**: $0.0001/request (2M requests free)
- **Cloud SQL**: $15-30/month (basic instance)
- **Secret Manager**: $0.06/secret/month (~$2-3/month)
- **Cloud Storage**: $0.02/GB/month (minimal for logs)
- **Total**: $20-40/month for development/production

### Scaling Strategy
- **Cloud Run**: Automatic scaling (0-1000 instances)
- **Database**: Vertical scaling or read replicas as needed
- **Storage**: Archive old data to Cloud Storage

## Monitoring & Observability

### Cloud Run Metrics
- Request count, latency, error rates
- CPU/memory utilization
- Instance count and scaling events

### Database Monitoring
- Connection count and query performance
- Storage usage and backup status
- Slow query logs

### Logging
- Application logs to Cloud Logging
- Structured logging with request IDs
- Error alerting via Cloud Monitoring

## Setup Instructions

### Prerequisites
1. Google Cloud Project with billing enabled
2. GitHub repository with Actions enabled
3. Python 3.11 development environment

### Initial Setup
```bash
# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable storage.googleapis.com

# Create Cloud SQL instance
gcloud sql instances create med13-db \
  --database-version=POSTGRES_15 \
  --cpu=1 \
  --memory=3840MB \
  --region=us-central1 \
  --root-password=[SECURE_PASSWORD]

# Create database
gcloud sql databases create med13_library --instance=med13-db

# Create data retention buckets
gsutil mb -p YOUR_PROJECT -c standard gs://med13-data-sources
gsutil lifecycle set retention-policy-90-days gs://med13-data-sources
gsutil mb -p YOUR_PROJECT -c coldline gs://med13-data-archive
```

### Deployment
1. Push code to GitHub main branch
2. GitHub Actions automatically runs tests, security scans, and deploys to staging
3. Create GitHub release to deploy to production
4. Monitor deployments in Cloud Console > Cloud Run:
   - `med13-resource-library` (public API)
   - `med13-resource-library-staging` (staging API)
   - `med13-curation` (curation UI)

### Post-Deployment Configuration
1. Set up custom domain (optional)
2. Configure monitoring alerts
3. Set up backup schedules
4. Create additional environments (staging, dev)

## Maintenance & Operations

### Backup Strategy
- **Database**: Daily automated backups via Cloud SQL
- **Application**: Infrastructure as code in GitHub
- **Secrets**: Versioned in Secret Manager

### Update Process
1. Make code changes
2. Push to feature branch
3. Create pull request
4. Automated testing runs
5. Merge to main triggers deployment

### Disaster Recovery
- **Database**: Point-in-time recovery available
- **Application**: Rollback via GitHub deployments
- **Data**: Regular exports to Cloud Storage

## Future Considerations

### Potential Enhancements
- **Multi-region deployment** for global availability
- **Cloud Armor** for DDoS protection
- **Memorystore** for caching frequently accessed data
- **Dataflow** for complex ETL pipelines
- **Vertex AI** for ML-powered curation assistance

### Scaling Triggers
- Monitor usage patterns for 3-6 months
- Consider read replicas for high read workloads
- Evaluate Cloud Run Jobs for batch processing
- Plan for multi-region expansion as user base grows

## Compliance & Security Notes

While not currently required, prepare for future healthcare compliance:
- **HIPAA**: Data encryption and access controls
- **GDPR**: Data subject rights and consent management
- **Audit Logging**: Comprehensive activity tracking
- **Data Residency**: Geographic data storage requirements

## Data Retention Policy

### Retention Guidelines
- **Raw source files**: Store in Cloud Storage bucket with 90-day retention
- **Processed data**: Retain indefinitely in Cloud SQL for research integrity
- **Audit logs**: 7-year retention for compliance and provenance tracking
- **Backups**: 30-day retention with weekly long-term archives
- **Temporary files**: Immediate deletion after processing

### Cloud Storage Setup
```bash
# Create data sources bucket with retention policy
gsutil mb -p YOUR_PROJECT -c standard gs://med13-data-sources
gsutil lifecycle set retention-policy-90-days gs://med13-data-sources

# Create archive bucket for long-term storage
gsutil mb -p YOUR_PROJECT -c coldline gs://med13-data-archive
```

### Database Backup Strategy
- **Automated backups**: Daily via Cloud SQL
- **Point-in-time recovery**: 7-day window available
- **Cross-region replication**: For disaster recovery (future enhancement)

## Infrastructure-as-Code Foundation

### Current Manual Setup (Terraform Migration Ready)
Document all manual setup commands for future Infrastructure-as-Code conversion:

```bash
# Enable required APIs
gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com

# Create Cloud SQL instance
gcloud sql instances create med13-db \
  --database-version=POSTGRES_15 \
  --tier=db-g1-small \
  --region=us-central1 \
  --backup-start-time=02:00

# Create database
gcloud sql databases create med13_library --instance=med13-db

# Deploy Cloud Run services
gcloud run deploy med13-resource-library \
  --source . \
  --region=us-central1 \
  --allow-unauthenticated=false \
  --service-account med13-prod@YOUR_PROJECT.iam.gserviceaccount.com

gcloud run deploy med13-curation \
  --source . \
  --region=us-central1 \
  --allow-unauthenticated=false \
  --service-account med13-prod@YOUR_PROJECT.iam.gserviceaccount.com
```

### Future IaC Options
- **Terraform**: For comprehensive infrastructure management
- **Pulumi**: For multi-cloud support and programming languages
- **Google Cloud Deployment Manager**: For GCP-native solutions

---



*This infrastructure guide should be reviewed and updated as the application evolves and scaling requirements change.*
