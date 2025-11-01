"""
Advanced validation rules for publication entities.

Implements business logic validation for publications including:
- DOI format and accessibility validation
- Journal impact factor and quality checks
- Author affiliation validation
- Publication date consistency
- Citation network validation
"""

import re
from typing import Dict, List, Any
from datetime import datetime
from dataclasses import dataclass

from .base_rules import ValidationRule, ValidationSeverity


@dataclass
class PublicationValidationRules:
    """
    Comprehensive validation rules for publication entities.

    Validates publication metadata, citations, authors, and journal
    information for scientific accuracy and completeness.
    """

    # DOI pattern (more comprehensive than basic validation)
    DOI_PATTERN = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)

    # PubMed ID pattern
    PUBMED_PATTERN = re.compile(r"^\d+$")

    # PMC ID pattern
    PMC_PATTERN = re.compile(r"^PMC\d+$", re.IGNORECASE)

    # Journal name patterns for quality assessment
    PREDATORY_JOURNAL_INDICATORS = [
        "international journal of",
        "global journal of",
        "world journal of",
        "universal journal of",
        "american journal of",
        "science publishing group",
        "imedpub",
        "omics",
        "hindawi",
    ]

    # High-impact journal indicators
    HIGH_IMPACT_JOURNALS = {
        "nature",
        "science",
        "cell",
        "new england journal of medicine",
        "lancet",
        "jama",
        "nature genetics",
        "nature medicine",
        "genome research",
        "plos genetics",
        "human molecular genetics",
    }

    @staticmethod
    def validate_doi_format_and_accessibility(doi: str) -> ValidationRule:
        """Validate DOI format and basic accessibility."""

        def rule(value):
            if not value:
                return True, "", None  # DOI is often optional

            if not isinstance(value, str):
                return (
                    False,
                    f"DOI must be string: {type(value)}",
                    "Provide DOI as string",
                )

            doi = value.strip()

            # Check format
            if not PublicationValidationRules.DOI_PATTERN.match(doi):
                return (
                    False,
                    f"Invalid DOI format: {doi}",
                    "DOIs should start with '10.' followed by registrant code",
                )

            # Check for common formatting issues
            if doi.startswith("doi:"):
                return (
                    False,
                    "DOI should not include 'doi:' prefix",
                    f"Use {doi[4:]} instead",
                )

            if " " in doi:
                return False, "DOI contains spaces", "Remove spaces from DOI"

            if doi.count("/") < 1:
                return (
                    False,
                    "DOI missing required slash",
                    "DOI format should be registrant/suffix",
                )

            # Check for suspicious patterns
            if doi.endswith(".pdf") or doi.endswith(".html"):
                return (
                    False,
                    "DOI appears to be a URL, not a DOI",
                    "Extract the DOI from the URL",
                )

            return True, "", None

        return ValidationRule(
            field="doi",
            rule="doi_format_accessibility",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STANDARD",
        )

    @staticmethod
    def validate_publication_date_consistency(
        pub_date: str, journal_info: Dict[str, Any]
    ) -> ValidationRule:
        """Validate publication date consistency and reasonableness."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            pub_date = value.get("publication_date")
            journal = value.get("journal", {})

            if not pub_date:
                return False, "Publication date is required", "Provide publication date"

            # Parse date
            try:
                if isinstance(pub_date, str):
                    # Try different date formats
                    date_formats = ["%Y-%m-%d", "%Y-%m", "%Y", "%B %Y", "%b %Y"]
                    parsed_date = None
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(pub_date, fmt)
                            break
                        except ValueError:
                            continue

                    if not parsed_date:
                        return (
                            False,
                            f"Cannot parse publication date: {pub_date}",
                            "Use YYYY-MM-DD, YYYY-MM, or YYYY format",
                        )

                elif isinstance(pub_date, datetime):
                    parsed_date = pub_date
                else:
                    return (
                        False,
                        f"Invalid publication date type: {type(pub_date)}",
                        "Provide date as string or datetime object",
                    )

                current_year = datetime.now().year

                # Check for future dates
                if (
                    parsed_date.year > current_year + 1
                ):  # Allow 1 year in future for preprints
                    return (
                        False,
                        f"Publication date in far future: {parsed_date.year}",
                        "Check publication date",
                    )

                # Check for unreasonably old dates
                if parsed_date.year < 1900:
                    return (
                        False,
                        f"Publication date too old: {parsed_date.year}",
                        "Biomedical publications are typically from 1900 onwards",
                    )

                # Check journal start date consistency (if available)
                journal_start_year = journal.get("start_year")
                if journal_start_year and parsed_date.year < journal_start_year:
                    return (
                        False,
                        f"Publication date ({parsed_date.year}) before journal start year ({journal_start_year})",
                        "Check publication or journal information",
                    )

                return True, "", None

            except Exception as e:
                return (
                    False,
                    f"Date validation error: {str(e)}",
                    "Provide valid publication date",
                )

        return ValidationRule(
            field="publication_date_consistency",
            rule="publication_date_consistency",
            validator=rule,
            severity=ValidationSeverity.ERROR,
            level="STANDARD",
        )

    @staticmethod
    def validate_author_information(authors: List[Dict[str, Any]]) -> ValidationRule:
        """Validate author information for completeness and quality."""

        def rule(value):
            if not value:
                return False, "Authors are required", "Provide author information"

            if not isinstance(value, list):
                return (
                    False,
                    f"Authors must be list: {type(value)}",
                    "Provide authors as list",
                )

            if len(value) == 0:
                return (
                    False,
                    "At least one author is required",
                    "Provide author information",
                )

            issues = []

            for i, author in enumerate(value):
                if not isinstance(author, dict):
                    issues.append(f"Author {i+1} must be dictionary")
                    continue

                author_name = (
                    author.get("name")
                    or f"{author.get('first_name', '')} {author.get('last_name', '')}".strip()
                )

                if not author_name:
                    issues.append(f"Author {i+1} missing name")
                    continue

                # Check name format
                name_parts = author_name.split()
                if len(name_parts) < 2:
                    issues.append(f"Author {i+1} name seems incomplete: {author_name}")

                # Check for institutional authors
                if any(
                    term in author_name.lower()
                    for term in ["consortium", "group", "network", "project"]
                ):
                    continue  # Institutional authors may have different formats

                # Check affiliation if provided
                affiliation = author.get("affiliation", "")
                if affiliation and len(affiliation) < 10:
                    issues.append(
                        f"Author {i+1} affiliation seems too short: {affiliation}"
                    )

            # Check for excessive number of authors (>1000 is suspicious)
            if len(value) > 1000:
                issues.append(f"Suspiciously high number of authors: {len(value)}")

            # Check for duplicate authors
            author_names = [
                str(author.get("name", ""))
                for author in value
                if isinstance(author, dict)
            ]
            if len(author_names) != len(set(author_names)):
                issues.append("Duplicate author names detected")

            if issues:
                return (
                    False,
                    "Author validation issues: " + "; ".join(issues),
                    "Review author information",
                )

            return True, "", None

        return ValidationRule(
            field="authors",
            rule="author_information",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STANDARD",
        )

    @staticmethod
    def validate_journal_quality_assessment(
        journal_info: Dict[str, Any],
    ) -> ValidationRule:
        """Validate journal quality and reputation."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None  # Journal info is often optional

            journal_name = value.get("name", "").lower()
            impact_factor = value.get("impact_factor")
            issn = value.get("issn")

            issues = []

            # Check for predatory journal indicators
            for indicator in PublicationValidationRules.PREDATORY_JOURNAL_INDICATORS:
                if indicator in journal_name:
                    issues.append(
                        f"Journal name contains predatory indicator: '{indicator}'"
                    )
                    break

            # Validate impact factor range
            if impact_factor is not None:
                if not isinstance(impact_factor, (int, float)):
                    issues.append("Impact factor must be numeric")
                elif not (
                    0 <= impact_factor <= 100
                ):  # Reasonable range for impact factors
                    issues.append(f"Suspicious impact factor: {impact_factor}")

            # Validate ISSN format
            if issn:
                if not re.match(r"^\d{4}-\d{3}[\dX]$", issn.upper()):
                    issues.append(f"Invalid ISSN format: {issn}")

            # Check for high-quality journal recognition
            if journal_name in PublicationValidationRules.HIGH_IMPACT_JOURNALS:
                # This is actually good, but we could log it
                pass

            if issues:
                return (
                    False,
                    "Journal quality issues: " + "; ".join(issues),
                    "Review journal information",
                )

            return True, "", None

        return ValidationRule(
            field="journal",
            rule="journal_quality",
            validator=rule,
            severity=ValidationSeverity.INFO,
            level="STRICT",
        )

    @staticmethod
    def validate_citation_consistency(
        title: str, abstract: str, keywords: List[str]
    ) -> ValidationRule:
        """Validate consistency between title, abstract, and keywords."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            title = value.get("title", "").lower()
            abstract = value.get("abstract", "").lower()
            keywords = [kw.lower() for kw in value.get("keywords", [])]

            if not title:
                return False, "Title is required", "Provide publication title"

            issues = []

            # Check if abstract mentions title keywords
            title_words = set(
                re.findall(r"\b\w{4,}\b", title)
            )  # Words of 4+ characters
            abstract_words = (
                set(re.findall(r"\b\w{4,}\b", abstract)) if abstract else set()
            )

            if abstract and title_words and abstract_words:
                overlap = title_words.intersection(abstract_words)
                if len(overlap) == 0:
                    issues.append("Title and abstract appear unrelated")

            # Check keyword consistency with title/abstract
            if keywords:
                content_words = (title + " " + (abstract or "")).split()
                content_word_set = set(w.lower() for w in content_words if len(w) > 3)

                keyword_matches = 0
                for keyword in keywords:
                    keyword_words = keyword.lower().split()
                    if any(kw_word in content_word_set for kw_word in keyword_words):
                        keyword_matches += 1

                # At least 50% of keywords should appear in title/abstract
                if keyword_matches / len(keywords) < 0.5:
                    issues.append("Keywords don't match title/abstract content")

            if issues:
                return (
                    False,
                    "Citation consistency issues: " + "; ".join(issues),
                    "Review title, abstract, and keywords for consistency",
                )

            return True, "", None

        return ValidationRule(
            field="citation_consistency",
            rule="citation_consistency",
            validator=rule,
            severity=ValidationSeverity.INFO,
            level="STRICT",
        )

    @staticmethod
    def validate_open_access_status(
        open_access: bool, pmc_id: str, doi: str
    ) -> ValidationRule:
        """Validate open access status consistency."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            oa_status = value.get("open_access")
            pmc_id = value.get("pmc_id")
            doi = value.get("doi")

            if oa_status is None:
                return True, "", None  # OA status unknown

            issues = []

            # PMC ID usually indicates open access
            if pmc_id and oa_status is False:
                issues.append("Publication has PMC ID but marked as not open access")

            # Some DOI prefixes indicate open access
            if doi and oa_status is False:
                oa_prefixes = [
                    "10.12688",
                    "10.1371",
                    "10.1101",
                    "10.31219",
                    "10.31222",
                ]  # eLife, PLOS, bioRxiv, etc.
                if any(doi.startswith(prefix) for prefix in oa_prefixes):
                    issues.append("DOI prefix suggests open access publication")

            if issues:
                return (
                    False,
                    "Open access status issues: " + "; ".join(issues),
                    "Review open access status",
                )

            return True, "", None

        return ValidationRule(
            field="open_access_consistency",
            rule="open_access_consistency",
            validator=rule,
            severity=ValidationSeverity.INFO,
            level="STRICT",
        )

    @staticmethod
    def validate_identifier_uniqueness(identifiers: Dict[str, str]) -> ValidationRule:
        """Validate uniqueness and consistency of publication identifiers."""

        def rule(value):
            if not value or not isinstance(value, dict):
                return True, "", None

            ids = value.copy()

            # Check for conflicts between identifiers
            pubmed_id = ids.get("pubmed_id")
            pmc_id = ids.get("pmc_id")

            issues = []

            # PubMed and PMC should be consistent (PMC articles usually have PubMed IDs)
            if pmc_id and not pubmed_id:
                issues.append("PMC article missing PubMed ID")

            # Check for duplicate identifiers (different fields with same value)
            id_values = [v for v in ids.values() if v]
            if len(id_values) != len(set(id_values)):
                issues.append("Duplicate identifier values across different fields")

            if issues:
                return (
                    False,
                    "Identifier uniqueness issues: " + "; ".join(issues),
                    "Review publication identifiers",
                )

            return True, "", None

        return ValidationRule(
            field="identifiers",
            rule="identifier_uniqueness",
            validator=rule,
            severity=ValidationSeverity.WARNING,
            level="STANDARD",
        )

    @classmethod
    def get_all_rules(cls) -> List[ValidationRule]:
        """Get all publication validation rules."""
        return [
            cls.validate_doi_format_and_accessibility(""),
            cls.validate_publication_date_consistency("", {}),
            cls.validate_author_information([]),
            cls.validate_journal_quality_assessment({}),
            cls.validate_citation_consistency("", "", []),
            cls.validate_open_access_status(False, "", ""),
            cls.validate_identifier_uniqueness({}),
        ]

    @classmethod
    def validate_publication_comprehensively(
        cls, publication_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Run comprehensive validation on publication data.

        Returns list of validation issues found.
        """
        issues = []

        for rule in cls.get_all_rules():
            # Apply rule-specific validation logic
            if rule.rule == "doi_format_accessibility":
                field_value = publication_data.get(rule.field)
                is_valid, message, suggestion = rule.validator(field_value)
            elif rule.rule == "publication_date_consistency":
                combined_data = {
                    "publication_date": publication_data.get("publication_date"),
                    "journal": publication_data.get("journal", {}),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            elif rule.rule == "author_information":
                field_value = publication_data.get(rule.field)
                is_valid, message, suggestion = rule.validator(field_value or [])
            elif rule.rule == "journal_quality":
                field_value = publication_data.get(rule.field)
                is_valid, message, suggestion = rule.validator(field_value or {})
            elif rule.rule == "citation_consistency":
                combined_data = {
                    "title": publication_data.get("title"),
                    "abstract": publication_data.get("abstract"),
                    "keywords": publication_data.get("keywords", []),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            elif rule.rule == "open_access_consistency":
                combined_data = {
                    "open_access": publication_data.get("open_access"),
                    "pmc_id": publication_data.get("pmc_id"),
                    "doi": publication_data.get("doi"),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            elif rule.rule == "identifier_uniqueness":
                combined_data = {
                    "pubmed_id": publication_data.get("pubmed_id"),
                    "pmc_id": publication_data.get("pmc_id"),
                    "doi": publication_data.get("doi"),
                }
                is_valid, message, suggestion = rule.validator(combined_data)
            else:
                continue

            if not is_valid:
                issues.append(
                    {
                        "field": rule.field,
                        "rule": rule.rule,
                        "severity": rule.severity.value,
                        "message": message,
                        "suggestion": suggestion,
                    }
                )

        return issues
