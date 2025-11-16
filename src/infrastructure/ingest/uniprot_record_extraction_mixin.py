"""Extraction helpers for UniProt records."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from src.type_definitions.common import RawRecord


class UniProtRecordExtractionMixin:
    def _extract_protein_name(self, record: RawRecord) -> str | None:  # noqa: C901
        """Extract recommended protein name."""
        try:
            protein_desc = record.get("proteinDescription")
            if not isinstance(protein_desc, dict):
                return None

            recommended_name = protein_desc.get("recommendedName")
            if isinstance(recommended_name, dict):
                full_name = recommended_name.get("fullName")
                if isinstance(full_name, dict):
                    value = full_name.get("value")
                    if isinstance(value, str):
                        return value

            # Fallback to submitted names
            submitted_names = protein_desc.get("submissionNames")
            if isinstance(submitted_names, list):
                for submitted_name in submitted_names:
                    if not isinstance(submitted_name, dict):
                        continue
                    full_name = submitted_name.get("fullName")
                    if isinstance(full_name, dict):
                        value = full_name.get("value")
                        if isinstance(value, str):
                            return value

        except Exception:
            logger.exception("Failed to extract protein name")
        return None

    def _extract_gene_name(self, record: RawRecord) -> str | None:  # noqa: C901
        """Extract primary gene name."""
        try:
            genes = record.get("genes")
            if not isinstance(genes, list):
                return None
            for gene in genes:
                if not isinstance(gene, dict):
                    continue
                if gene.get("type") == "primary":
                    gene_name = gene.get("geneName")
                    if isinstance(gene_name, dict):
                        value = gene_name.get("value")
                        if isinstance(value, str):
                            return value
            # Fallback to first gene name
            for gene in genes:
                if not isinstance(gene, dict):
                    continue
                gene_name = gene.get("geneName")
                if isinstance(gene_name, dict):
                    value = gene_name.get("value")
                    if isinstance(value, str):
                        return value
        except Exception:
            logger.exception("Failed to extract gene name")
        return None

    def _extract_organism(
        self,
        record: RawRecord,
    ) -> dict[str, str | None] | None:
        """Extract organism information."""
        try:
            organism = record.get("organism")
            if not isinstance(organism, dict):
                return None
            scientific_name = organism.get("scientificName")
            common_name = organism.get("commonName")
            taxon_id = organism.get("taxonId")
            result: dict[str, str | None] = {}
            if isinstance(scientific_name, str):
                result["scientific_name"] = scientific_name
            else:
                result["scientific_name"] = None
            if isinstance(common_name, str):
                result["common_name"] = common_name
            else:
                result["common_name"] = None
            if isinstance(taxon_id, str):
                result["taxon_id"] = taxon_id
            else:
                result["taxon_id"] = None
        except Exception:
            logger.exception("Failed to extract organism info")
        else:
            return result
        return None

    def _extract_sequence(self, record: RawRecord) -> RawRecord | None:
        """Extract protein sequence information."""
        try:
            sequence = record.get("sequence")
            if not isinstance(sequence, dict):
                return None
            return {
                "length": sequence.get("length"),
                "mol_weight": sequence.get("molWeight"),
                "crc64": sequence.get("crc64"),
                "md5": sequence.get("md5"),
                # Note: Full sequence would be in separate endpoint if needed
            }
        except Exception:
            logger.exception("Failed to extract sequence info")
        return None

    def _extract_function(self, record: RawRecord) -> list[str]:
        """Extract protein function descriptions."""
        functions: list[str] = []
        try:
            comments = record.get("comments")
            if not isinstance(comments, list):
                return functions
            for comment in comments:
                if not isinstance(comment, dict):
                    continue
                if comment.get("commentType") != "FUNCTION":
                    continue
                texts = comment.get("texts")
                if not isinstance(texts, list):
                    continue
                for text in texts:
                    if not isinstance(text, dict):
                        continue
                    value = text.get("value")
                    if isinstance(value, str):
                        functions.append(value)
        except Exception:
            logger.exception("Failed to extract function list")
        return functions

    def _extract_subcellular_location(  # noqa: C901
        self,
        record: RawRecord,
    ) -> list[str]:
        """Extract subcellular location information."""
        locations: list[str] = []
        try:
            comments = record.get("comments")
            if not isinstance(comments, list):
                return locations
            for comment in comments:
                if not isinstance(comment, dict):
                    continue
                if comment.get("commentType") != "SUBCELLULAR LOCATION":
                    continue
                sub_locations = comment.get("subcellularLocations")
                if not isinstance(sub_locations, list):
                    continue
                for location in sub_locations:
                    if not isinstance(location, dict):
                        continue
                    location_info = location.get("location")
                    if not isinstance(location_info, dict):
                        continue
                    location_desc = location_info.get("value")
                    if isinstance(location_desc, str):
                        locations.append(location_desc)
        except Exception:
            logger.exception("Failed to extract subcellular locations")
        return locations

    def _extract_pathway(self, record: RawRecord) -> list[str]:
        """Extract pathway information."""
        pathways: list[str] = []
        try:
            comments = record.get("comments")
            if not isinstance(comments, list):
                return pathways
            for comment in comments:
                if not isinstance(comment, dict):
                    continue
                if comment.get("commentType") != "PATHWAY":
                    continue
                texts = comment.get("texts")
                if not isinstance(texts, list):
                    continue
                for text in texts:
                    if not isinstance(text, dict):
                        continue
                    value = text.get("value")
                    if isinstance(value, str):
                        pathways.append(value)
        except Exception:
            logger.exception("Failed to extract pathways")
        return pathways

    def _extract_disease_associations(
        self,
        record: RawRecord,
    ) -> list[RawRecord]:
        """Extract disease associations."""
        diseases: list[RawRecord] = []
        try:
            comments = record.get("comments")
            if not isinstance(comments, list):
                return diseases
            for comment in comments:
                if not isinstance(comment, dict):
                    continue
                if comment.get("commentType") != "DISEASE":
                    continue
                disease = comment.get("disease")
                if not isinstance(disease, dict):
                    continue
                diseases.append(
                    {
                        "name": disease.get("diseaseName"),
                        "description": disease.get("description"),
                        "acronym": disease.get("acronym"),
                        "id": disease.get("diseaseId"),
                    },
                )
        except Exception:
            logger.exception("Failed to extract disease associations")
        return diseases

    def _extract_isoforms(self, record: RawRecord) -> list[RawRecord]:
        """Extract isoform information."""
        isoforms: list[RawRecord] = []
        try:
            isoform_refs = record.get("isoforms")
            if not isinstance(isoform_refs, list):
                return isoforms
            for isoform_ref in isoform_refs:
                if not isinstance(isoform_ref, dict):
                    continue
                isoform_ids = isoform_ref.get("isoformIds")
                if not isinstance(isoform_ids, list) or not isoform_ids:
                    continue
                isoform = isoform_ids[0]
                if isinstance(isoform, dict):
                    isoforms.append(
                        {
                            "name": isoform.get("value"),
                            "sequence_ids": isoform_ref.get("isoformSequenceIds", []),
                        },
                    )
        except Exception:
            logger.exception("Failed to extract isoforms")
        return isoforms

    def _extract_domains(self, record: RawRecord) -> list[RawRecord]:
        """Extract domain information."""
        domains: list[RawRecord] = []
        try:
            features = record.get("features")
            if not isinstance(features, list):
                return domains
            for feature in features:
                if not isinstance(feature, dict):
                    continue
                if feature.get("type") != "DOMAIN":
                    continue
                location = feature.get("location")
                if isinstance(location, dict):
                    start = location.get("start")
                    start_value = (
                        start.get("value") if isinstance(start, dict) else None
                    )
                    end = location.get("end")
                    end_value = end.get("value") if isinstance(end, dict) else None
                else:
                    start_value = None
                    end_value = None
                domains.append(
                    {
                        "name": feature.get("description"),
                        "start": start_value,
                        "end": end_value,
                    },
                )
        except Exception:
            logger.exception("Failed to extract domains")
        return domains

    def _extract_ptm_sites(self, record: RawRecord) -> list[RawRecord]:
        """Extract post-translational modification sites."""
        ptm_sites: list[RawRecord] = []
        try:
            features = record.get("features")
            if not isinstance(features, list):
                return ptm_sites
            ptm_types = ["MODIFIED RESIDUE", "CROSSLNK", "LIPID BINDING SITE"]
            for feature in features:
                if not isinstance(feature, dict):
                    continue
                if feature.get("type") not in ptm_types:
                    continue
                location = feature.get("location")
                position_value = None
                if isinstance(location, dict):
                    position = location.get("position")
                    if isinstance(position, dict):
                        position_value = position.get("value")
                ptm_sites.append(
                    {
                        "type": feature.get("type"),
                        "description": feature.get("description"),
                        "position": position_value,
                    },
                )
        except Exception:
            logger.exception("Failed to extract PTM sites")
        return ptm_sites

    def _extract_interactions(self, record: RawRecord) -> list[RawRecord]:
        """Extract protein interaction information."""
        interactions: list[RawRecord] = []
        try:
            comments = record.get("comments")
            if not isinstance(comments, list):
                return interactions
            for comment in comments:
                if not isinstance(comment, dict):
                    continue
                if comment.get("commentType") != "INTERACTION":
                    continue
                interactants = comment.get("interactions")
                if not isinstance(interactants, list):
                    continue
                for interaction in interactants:
                    if not isinstance(interaction, dict):
                        continue
                    interactant = interaction.get("interactant")
                    interactant_value = (
                        interactant.get("value")
                        if isinstance(interactant, dict)
                        else None
                    )
                    interactions.append(
                        {
                            "interactant": interactant_value,
                            "label": interaction.get("label"),
                        },
                    )
        except Exception:
            logger.exception("Failed to extract interactions")
        return interactions

    def _extract_references(self, record: RawRecord) -> list[RawRecord]:
        """Extract reference information."""
        references: list[RawRecord] = []
        try:
            citations = record.get("references")
            if not isinstance(citations, list):
                return references
            for citation in citations:
                if not isinstance(citation, dict):
                    continue
                ref = citation.get("citation")
                if not isinstance(ref, dict):
                    continue
                authors = ref.get("authors")
                author_names: list[str] = []
                if isinstance(authors, list):
                    for author in authors:
                        if isinstance(author, dict):
                            name = author.get("name")
                            if isinstance(name, str):
                                author_names.append(name)
                publication_date_info = ref.get("publicationDate")
                publication_date_value = (
                    publication_date_info.get("value")
                    if isinstance(publication_date_info, dict)
                    else None
                )

                references.append(
                    {
                        "title": ref.get("title"),
                        "authors": author_names,
                        "journal": ref.get("journal"),
                        "publication_date": publication_date_value,
                        "pubmed_id": ref.get("pubmedId"),
                        "doi": ref.get("doiId"),
                    },
                )
        except Exception:
            logger.exception("Failed to extract references")
        return references
