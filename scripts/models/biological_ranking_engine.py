from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RankingColumns:
    """Column names used by the biological ranking engine."""

    fragmentation: str = "fragment_score"
    score: str = "score"
    isotope_similarity: str = "isotope_similarity"
    mass_error_ppm: str = "mass_error_ppm"
    formula: str = "formula"


class BiologicalRankingEngine:
    """Biological ladder ranking workflow.

    Ladder order:
    1) fragmentation DESC
    2) score DESC
    3) isotope_similarity DESC
    4) mass_error_ppm ASC (absolute value)
    5) formula ASC
    6) full ties are preserved for deterministic downstream processing
    """

    def __init__(self, columns: RankingColumns | None = None) -> None:
        self.columns = columns or RankingColumns()

    def apply_ranking(self, df: pd.DataFrame, group_by: str | Sequence[str]) -> pd.DataFrame:
        """Apply ranking by group and return all rows with tie metadata.

        Output columns added:
        - rank_group (int): rank inside each group (1..N)
        - is_tied (bool): True when there is a full tie for the same rank

        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")

        group_columns = self._normalize_group_by(group_by)
        self._validate_required_columns(df, group_columns)
        return self._rank_group(df.copy(), group_columns)

    def format_for_display(
        self,
        df: pd.DataFrame,
        group_by: str | Sequence[str] | None = None,
    ) -> pd.DataFrame:
        """Prepare a deterministic dataframe for UI/report display."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")

        if "rank_group" not in df.columns or "is_tied" not in df.columns:
            raise ValueError("DataFrame must contain 'rank_group' and 'is_tied'.")

        display_df = df.copy()
        if group_by is not None:
            group_columns = self._normalize_group_by(group_by)
            self._validate_required_columns(display_df, group_columns)
            sort_cols = [*group_columns, "rank_group", self.columns.formula]
        else:
            sort_cols = ["rank_group"]

        return display_df.sort_values(sort_cols, kind="stable").reset_index(drop=True)

    def _rank_group(self, df: pd.DataFrame, group_columns: Sequence[str]) -> pd.DataFrame:
        frag_col = self.columns.fragmentation
        score_col = self.columns.score
        iso_col = self.columns.isotope_similarity
        mass_col = self.columns.mass_error_ppm
        formula_col = self.columns.formula

        df[frag_col] = pd.to_numeric(df[frag_col], errors="coerce")
        df[score_col] = pd.to_numeric(df[score_col], errors="coerce")
        df[iso_col] = pd.to_numeric(df[iso_col], errors="coerce")
        df[mass_col] = pd.to_numeric(df[mass_col], errors="coerce")

        # Helper columns keep tie detection explicit and deterministic.
        df["_rank_fragmentation"] = df[frag_col]
        df["_rank_score"] = df[score_col]
        df["_rank_isotope"] = df[iso_col]
        df["_rank_mass_abs"] = df[mass_col].abs()
        df["_rank_formula"] = df[formula_col].fillna("").astype(str).str.strip().str.casefold()
        df["_stable_row_order"] = np.arange(len(df), dtype=int)

        ordered = df.sort_values(
            [
                *group_columns,
                "_rank_fragmentation",
                "_rank_score",
                "_rank_isotope",
                "_rank_mass_abs",
                "_rank_formula",
                "_stable_row_order",
            ],
            ascending=[True] * len(group_columns) + [False, False, False, True, True, True],
            na_position="last",
            kind="stable",
        ).copy()

        tie_cols = ["_rank_fragmentation", "_rank_score", "_rank_isotope", "_rank_mass_abs", "_rank_formula"]
        prev = ordered.groupby(list(group_columns), dropna=False, sort=False)[tie_cols].shift(1)

        same_as_previous = pd.Series(True, index=ordered.index, dtype=bool)
        for col in tie_cols:
            same_col = (ordered[col] == prev[col]) | (ordered[col].isna() & prev[col].isna())
            same_as_previous &= same_col

        first_in_group = (
            ordered.groupby(list(group_columns), dropna=False, sort=False).cumcount() == 0
        )
        is_new_rank = first_in_group | (~same_as_previous)
        ordered["rank_group"] = (
            is_new_rank.groupby([ordered[c] for c in group_columns], dropna=False).cumsum().astype(int)
        )

        tie_count = (
            ordered.groupby([*group_columns, *tie_cols], dropna=False, sort=False)[tie_cols[0]]
            .transform("size")
            .astype(int)
        )
        ordered["is_tied"] = tie_count > 1

        return ordered.drop(
            columns=[*tie_cols, "_stable_row_order"],
            errors="ignore",
        )

    def _normalize_group_by(self, group_by: str | Sequence[str]) -> list[str]:
        if isinstance(group_by, str):
            return [group_by]
        if not group_by:
            raise ValueError("group_by must not be empty")
        return list(group_by)

    def _validate_required_columns(
        self,
        df: pd.DataFrame,
        group_columns: Sequence[str],
    ) -> None:
        required = {
            *group_columns,
            self.columns.fragmentation,
            self.columns.score,
            self.columns.isotope_similarity,
            self.columns.mass_error_ppm,
            self.columns.formula,
        }
        missing = sorted(col for col in required if col not in df.columns)
        if missing:
            raise ValueError(f"Missing required columns for ranking: {missing}")
