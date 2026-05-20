"""Pacote de features.

Alguns ambientes deste projeto nao incluem o modulo opcional `views`.
Este import defensivo evita falha ao executar modulos como
`scripts.features.analytics` diretamente.
"""

try:  # pragma: no cover
    from .views import (  # noqa: F401
        batches_summary,
        features_by_batch,
        features_without_identification,
        top_candidates_by_batch,
        best_candidate_per_feature,
        mass_error_distribution,
        abundance_by_sample_group,
        replicate_overview,
        candidates_with_external_data,
        external_compounds_by_source,
        chemical_class_distribution,
        compound_properties,
        taxonomy_for_batch_candidates,
        staging_load_status,
        pubchem_staging_preview,
        chebi_staging_preview,
        score_statistics_by_batch,
        features_above_score_threshold,
        duplicate_molecular_formulas,
        top_candidates_per_feature,
        candidate_match_view,
    )
except ModuleNotFoundError:
    # Modulo opcional ausente no workspace atual.
    pass
