"""
Test script to verify that all ingestion APIs are returning real data
from external biomedical sources.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Final

from src.infrastructure.ingest import (
    ClinVarIngestor,
    HPOIngestor,
    IngestionCoordinator,
    PubMedIngestor,
    UniProtIngestor,
)

LOGGER_NAME: Final[str] = "med13.ingestion.real_apis"
logger = logging.getLogger(LOGGER_NAME)


def print_header(title: str):
    """Print a formatted header."""
    separator = "=" * 60
    logger.info("")
    logger.info(separator)
    logger.info(" %s", title)
    logger.info(separator)


def print_result_summary(result, source_name: str):
    """Print a summary of ingestion results."""
    logger.info("")
    logger.info("📊 %s RESULTS:", source_name.upper())
    logger.info("   Status: %s", result.status.value)
    logger.info("   Records processed: %s", result.records_processed)
    logger.info("   Records failed: %s", result.records_failed)
    logger.info("   Duration: %.2f seconds", result.duration_seconds)
    logger.info("   Errors: %s", len(result.errors))

    if result.errors:
        logger.info("   Error details:")
        for error in result.errors[:3]:  # Show first 3 errors
            logger.info("     - %s", error)

    if result.data:
        logger.info("   Sample data keys: %s...", list(result.data[0].keys())[:5])
        logger.info("   First record preview: %s...", str(result.data[0])[:200])


async def test_clinvar_real_data():
    """Test ClinVar ingestor with real API."""
    print_header("Testing ClinVar API - Real Genetic Variant Data")

    async with ClinVarIngestor() as ingestor:
        logger.info("🔍 Searching for MED13 variants in ClinVar...")

        result = await ingestor.ingest(max_results=5)  # Small limit for testing

        print_result_summary(result, "clinvar")

        # Verify we got real data
        if result.data and result.records_processed > 0:
            first_record = result.data[0]
            logger.info("")
            logger.info("✅ REAL DATA VERIFICATION:")
            logger.info("   Has clinvar_id: %s", "clinvar_id" in first_record)
            logger.info("   Has parsed_data: %s", "parsed_data" in first_record)
            if "clinvar_id" in first_record:
                logger.info("   Sample ClinVar ID: %s", first_record["clinvar_id"])

        return result.records_processed > 0


async def test_pubmed_real_data():
    """Test PubMed ingestor with real API."""
    print_header("Testing PubMed API - Real Scientific Literature")

    async with PubMedIngestor() as ingestor:
        logger.info("🔍 Searching for MED13 publications in PubMed...")

        result = await ingestor.ingest(max_results=3)  # Small limit for testing

        print_result_summary(result, "pubmed")

        # Verify we got real data
        if result.data and result.records_processed > 0:
            first_record = result.data[0]
            logger.info("")
            logger.info("✅ REAL DATA VERIFICATION:")
            logger.info("   Has pubmed_id: %s", "pubmed_id" in first_record)
            logger.info("   Has title: %s", "title" in first_record)
            logger.info("   Has authors: %s", "authors" in first_record)
            if first_record.get("title"):
                logger.info("   Sample title: %s...", first_record["title"][:100])

        return result.records_processed > 0


async def test_hpo_real_data():
    """Test HPO ingestor with real API."""
    print_header("Testing HPO API - Real Phenotype Ontology")

    async with HPOIngestor() as ingestor:
        logger.info("🔍 Loading HPO ontology data...")

        result = await ingestor.ingest(
            med13_only=False,  # Get full ontology, not just MED13 terms
        )

        print_result_summary(result, "hpo")

        # Verify we got real data
        if result.data and result.records_processed > 0:
            first_record = result.data[0]
            logger.info("")
            logger.info("✅ REAL DATA VERIFICATION:")
            logger.info("   Has hpo_id: %s", "hpo_id" in first_record)
            logger.info("   Has name: %s", "name" in first_record)
            logger.info("   Has definition: %s", "definition" in first_record)
            if "hpo_id" in first_record:
                logger.info("   Sample HPO ID: %s", first_record["hpo_id"])
            if "name" in first_record:
                logger.info("   Sample name: %s", first_record["name"])

        return result.records_processed > 0


async def test_uniprot_real_data():
    """Test UniProt ingestor with real API."""
    print_header("Testing UniProt API - Real Protein Data")

    async with UniProtIngestor() as ingestor:
        logger.info("🔍 Searching for MED13 protein in UniProt...")

        result = await ingestor.ingest(max_results=2)  # Small limit for testing

        print_result_summary(result, "uniprot")

        # Verify we got real data
        if result.data and result.records_processed > 0:
            first_record = result.data[0]
            logger.info("")
            logger.info("✅ REAL DATA VERIFICATION:")
            logger.info(
                "   Has primaryAccession: %s",
                "primaryAccession" in first_record,
            )
            logger.info(
                "   Has proteinDescription: %s",
                "proteinDescription" in first_record,
            )
            logger.info("   Has organism: %s", "organism" in first_record)
            if "primaryAccession" in first_record:
                logger.info(
                    "   Sample UniProt ID: %s",
                    first_record["primaryAccession"],
                )
            # Check nested protein name
            protein_desc = first_record.get("proteinDescription", {})
            rec_name = protein_desc.get("recommendedName", {})
            full_name = rec_name.get("fullName", {})
            protein_name = full_name.get("value")
            if protein_name:
                logger.info("   Sample protein name: %s...", protein_name[:50])

        return result.records_processed > 0


async def test_coordinator_real_data():
    """Test the ingestion coordinator with real APIs."""
    print_header("Testing Ingestion Coordinator - All Sources")

    def progress_callback(source, phase, progress):
        logger.info("📈 [%s] %s: %.1f%%", source, phase.value, progress)

    coordinator = IngestionCoordinator(
        max_concurrent_ingestors=2,  # Limit concurrency for testing
        progress_callback=progress_callback,
    )

    logger.info("🚀 Starting coordinated ingestion from all sources...")

    start_time = time.time()
    result = await coordinator.ingest_critical_sources_only(
        gene_symbol="MED13",
        max_results=5,  # Very small limit for quick testing
    )

    total_time = time.time() - start_time

    logger.info("")
    logger.info("🎯 COORDINATOR RESULTS:")
    logger.info("   Total sources: %s", result.total_sources)
    logger.info("   Completed: %s", result.completed_sources)
    logger.info("   Failed: %s", result.failed_sources)
    logger.info("   Total records: %s", result.total_records)
    logger.info("   Total time: %.2f seconds", total_time)
    if total_time > 0:
        logger.info(
            "   Records per second: %.2f",
            result.total_records / total_time,
        )
    else:
        logger.info("   Records per second: N/A")

    logger.info("")
    logger.info("📋 PER-SOURCE RESULTS:")
    for source, source_result in result.source_results.items():
        status = source_result.status.value
        records = source_result.records_processed
        duration = source_result.duration_seconds
        logger.info(
            "   %s: %s (%s records, %.2fs)",
            source,
            status,
            records,
            duration,
        )

    return result.total_records > 0


async def test_raw_data_storage():
    """Test that raw data is being stored."""
    print_header("Testing Raw Data Storage")

    raw_data_dir = Path("data/raw")
    logger.info("📁 Checking raw data directory: %s", raw_data_dir.absolute())

    if raw_data_dir.exists():
        logger.info("✅ Raw data directory exists")

        # Check what sources have data
        sources = [d.name for d in raw_data_dir.iterdir() if d.is_dir()]
        logger.info("📂 Sources with stored data: %s", sources)

        for source in sources:
            source_dir = raw_data_dir / source
            files = list(source_dir.glob("*.json"))
            if files:
                logger.info("   %s: %s files", source, len(files))
                # Show most recent file
                latest_file = max(files, key=lambda f: f.stat().st_mtime)
                logger.info("     Latest: %s", latest_file.name)
            else:
                logger.info("   %s: No files", source)
    else:
        logger.info("❌ Raw data directory does not exist")

    return raw_data_dir.exists()


async def main():
    """Run all real API tests."""
    logger.info("🧪 TESTING REAL API ENDPOINTS")
    logger.info("This will make actual HTTP requests to biomedical APIs")
    logger.info("Please ensure you have internet connectivity...\n")

    # Track test results
    results = {}

    try:
        # Test individual ingestors
        logger.info("🔬 Testing Individual Ingestors...")

        results["clinvar"] = await test_clinvar_real_data()
        await asyncio.sleep(1)  # Brief pause between tests

        results["pubmed"] = await test_pubmed_real_data()
        await asyncio.sleep(1)

        results["hpo"] = await test_hpo_real_data()
        await asyncio.sleep(1)

        results["uniprot"] = await test_uniprot_real_data()
        await asyncio.sleep(1)

        # Test coordinator
        results["coordinator"] = await test_coordinator_real_data()

        # Test data storage
        results["storage"] = await test_raw_data_storage()

    except KeyboardInterrupt:
        logger.info("")
        logger.info("⏹️  Testing interrupted by user")
        return
    except Exception:
        logger.exception("❌ Unexpected error during testing")
        return

    # Print final summary
    print_header("FINAL TEST SUMMARY")

    all_passed = all(results.values())

    logger.info("📈 Test Results:")
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info("   %s: %s", test_name, status)

    logger.info("")
    logger.info("🎯 OVERALL RESULT:")
    if all_passed:
        logger.info("   ✅ ALL TESTS PASSED - APIs are returning real data!")
        logger.info("   🎉 The ingestion infrastructure is working correctly.")
    else:
        failed_tests = [name for name, passed in results.items() if not passed]
        logger.info("   ❌ Some tests failed: %s", ", ".join(failed_tests))
        logger.info("   🔍 Check the output above for details.")

    logger.info("")
    logger.info("💡 NOTES:")
    logger.info("   - ClinVar/PubMed: May return 0 results if API limits are hit")
    logger.info("   - HPO: Should always return ontology data")
    logger.info("   - UniProt: May return 0 results for some queries")
    logger.info("   - Raw data is stored in data/raw/ directory")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(main())
