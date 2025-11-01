#!/usr/bin/env python3
"""
Test script to verify that all ingestion APIs are returning real data
from external biomedical sources.
"""

import asyncio
import time
from pathlib import Path

from src.infrastructure.ingest import (
    ClinVarIngestor,
    PubMedIngestor,
    HPOIngestor,
    UniProtIngestor,
    IngestionCoordinator,
)


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_result_summary(result, source_name: str):
    """Print a summary of ingestion results."""
    print(f"\n📊 {source_name.upper()} RESULTS:")
    print(f"   Status: {result.status.value}")
    print(f"   Records processed: {result.records_processed}")
    print(f"   Records failed: {result.records_failed}")
    print(f"   Duration: {result.duration_seconds:.2f} seconds")
    print(f"   Errors: {len(result.errors)}")

    if result.errors:
        print("   Error details:")
        for error in result.errors[:3]:  # Show first 3 errors
            print(f"     - {str(error)}")

    if result.data:
        print(f"   Sample data keys: {list(result.data[0].keys())[:5]}...")
        print(f"   First record preview: {str(result.data[0])[:200]}...")


async def test_clinvar_real_data():
    """Test ClinVar ingestor with real API."""
    print_header("Testing ClinVar API - Real Genetic Variant Data")

    async with ClinVarIngestor() as ingestor:
        print("🔍 Searching for MED13 variants in ClinVar...")

        result = await ingestor.ingest(max_results=5)  # Small limit for testing

        print_result_summary(result, "clinvar")

        # Verify we got real data
        if result.data and result.records_processed > 0:
            first_record = result.data[0]
            print("\n✅ REAL DATA VERIFICATION:")
            print(f"   Has clinvar_id: {'clinvar_id' in first_record}")
            print(f"   Has parsed_data: {'parsed_data' in first_record}")
            if "clinvar_id" in first_record:
                print(f"   Sample ClinVar ID: {first_record['clinvar_id']}")

        return result.records_processed > 0


async def test_pubmed_real_data():
    """Test PubMed ingestor with real API."""
    print_header("Testing PubMed API - Real Scientific Literature")

    async with PubMedIngestor() as ingestor:
        print("🔍 Searching for MED13 publications in PubMed...")

        result = await ingestor.ingest(max_results=3)  # Small limit for testing

        print_result_summary(result, "pubmed")

        # Verify we got real data
        if result.data and result.records_processed > 0:
            first_record = result.data[0]
            print("\n✅ REAL DATA VERIFICATION:")
            print(f"   Has pubmed_id: {'pubmed_id' in first_record}")
            print(f"   Has title: {'title' in first_record}")
            print(f"   Has authors: {'authors' in first_record}")
            if "title" in first_record and first_record["title"]:
                print(f"   Sample title: {first_record['title'][:100]}...")

        return result.records_processed > 0


async def test_hpo_real_data():
    """Test HPO ingestor with real API."""
    print_header("Testing HPO API - Real Phenotype Ontology")

    async with HPOIngestor() as ingestor:
        print("🔍 Loading HPO ontology data...")

        result = await ingestor.ingest(
            med13_only=False  # Get full ontology, not just MED13 terms
        )

        print_result_summary(result, "hpo")

        # Verify we got real data
        if result.data and result.records_processed > 0:
            first_record = result.data[0]
            print("\n✅ REAL DATA VERIFICATION:")
            print(f"   Has hpo_id: {'hpo_id' in first_record}")
            print(f"   Has name: {'name' in first_record}")
            print(f"   Has definition: {'definition' in first_record}")
            if "hpo_id" in first_record:
                print(f"   Sample HPO ID: {first_record['hpo_id']}")
            if "name" in first_record:
                print(f"   Sample name: {first_record['name']}")

        return result.records_processed > 0


async def test_uniprot_real_data():
    """Test UniProt ingestor with real API."""
    print_header("Testing UniProt API - Real Protein Data")

    async with UniProtIngestor() as ingestor:
        print("🔍 Searching for MED13 protein in UniProt...")

        result = await ingestor.ingest(max_results=2)  # Small limit for testing

        print_result_summary(result, "uniprot")

        # Verify we got real data
        if result.data and result.records_processed > 0:
            first_record = result.data[0]
            print("\n✅ REAL DATA VERIFICATION:")
            print(f"   Has primaryAccession: {'primaryAccession' in first_record}")
            print(f"   Has proteinDescription: {'proteinDescription' in first_record}")
            print(f"   Has organism: {'organism' in first_record}")
            if "primaryAccession" in first_record:
                print(f"   Sample UniProt ID: {first_record['primaryAccession']}")
            # Check nested protein name
            protein_desc = first_record.get("proteinDescription", {})
            rec_name = protein_desc.get("recommendedName", {})
            full_name = rec_name.get("fullName", {})
            protein_name = full_name.get("value")
            if protein_name:
                print(f"   Sample protein name: {protein_name[:50]}...")

        return result.records_processed > 0


async def test_coordinator_real_data():
    """Test the ingestion coordinator with real APIs."""
    print_header("Testing Ingestion Coordinator - All Sources")

    def progress_callback(source, phase, progress):
        print(f"📈 [{source}] {phase.value}: {progress:.1f}%")

    coordinator = IngestionCoordinator(
        max_concurrent_ingestors=2,  # Limit concurrency for testing
        progress_callback=progress_callback,
    )

    print("🚀 Starting coordinated ingestion from all sources...")

    start_time = time.time()
    result = await coordinator.ingest_critical_sources_only(
        gene_symbol="MED13",
        max_results=5,  # Very small limit for quick testing
    )

    total_time = time.time() - start_time

    print("\n🎯 COORDINATOR RESULTS:")
    print(f"   Total sources: {result.total_sources}")
    print(f"   Completed: {result.completed_sources}")
    print(f"   Failed: {result.failed_sources}")
    print(f"   Total records: {result.total_records}")
    print(f"   Total time: {total_time:.2f} seconds")
    print(
        f"   Records per second: {result.total_records / total_time:.2f}"
        if total_time > 0
        else "   Records per second: N/A"
    )

    print("\n📋 PER-SOURCE RESULTS:")
    for source, source_result in result.source_results.items():
        status = source_result.status.value
        records = source_result.records_processed
        duration = source_result.duration_seconds
        print(f"   {source}: {status} ({records} records, {duration:.2f}s)")

    return result.total_records > 0


async def test_raw_data_storage():
    """Test that raw data is being stored."""
    print_header("Testing Raw Data Storage")

    raw_data_dir = Path("data/raw")
    print(f"📁 Checking raw data directory: {raw_data_dir.absolute()}")

    if raw_data_dir.exists():
        print("✅ Raw data directory exists")

        # Check what sources have data
        sources = [d.name for d in raw_data_dir.iterdir() if d.is_dir()]
        print(f"📂 Sources with stored data: {sources}")

        for source in sources:
            source_dir = raw_data_dir / source
            files = list(source_dir.glob("*.json"))
            if files:
                print(f"   {source}: {len(files)} files")
                # Show most recent file
                latest_file = max(files, key=lambda f: f.stat().st_mtime)
                print(f"     Latest: {latest_file.name}")
            else:
                print(f"   {source}: No files")
    else:
        print("❌ Raw data directory does not exist")

    return raw_data_dir.exists()


async def main():
    """Run all real API tests."""
    print("🧪 TESTING REAL API ENDPOINTS")
    print("This will make actual HTTP requests to biomedical APIs")
    print("Please ensure you have internet connectivity...\n")

    # Track test results
    results = {}

    try:
        # Test individual ingestors
        print("🔬 Testing Individual Ingestors...")

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
        print("\n⏹️  Testing interrupted by user")
        return
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        return

    # Print final summary
    print_header("FINAL TEST SUMMARY")

    all_passed = all(results.values())

    print("📈 Test Results:")
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name}: {status}")

    print("\n🎯 OVERALL RESULT:")
    if all_passed:
        print("   ✅ ALL TESTS PASSED - APIs are returning real data!")
        print("   🎉 The ingestion infrastructure is working correctly.")
    else:
        failed_tests = [name for name, passed in results.items() if not passed]
        print(f"   ❌ Some tests failed: {', '.join(failed_tests)}")
        print("   🔍 Check the output above for details.")

    print("\n💡 NOTES:")
    print("   - ClinVar/PubMed: May return 0 results if API limits are hit")
    print("   - HPO: Should always return ontology data")
    print("   - UniProt: May return 0 results for some queries")
    print("   - Raw data is stored in data/raw/ directory")


if __name__ == "__main__":
    asyncio.run(main())
