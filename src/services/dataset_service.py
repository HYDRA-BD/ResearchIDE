"""Dataset Inspection and Management Service for ResearchIDE.

Provides local storage, CSV/TSV parsing, and descriptive statistics
without sending user data outside the local workstation.
"""
from __future__ import annotations
import csv
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from src.utils.logger import app_logger


@dataclass
class ColumnSummary:
    """Statistical summary of a single dataset column."""
    name: str
    dtype: str
    non_null_count: int
    null_count: int
    min_val: Optional[Any] = None
    max_val: Optional[Any] = None
    unique_count: int = 0


@dataclass
class DatasetSummary:
    """Summary and tabular preview of an imported research dataset."""
    file_name: str
    file_path: Path
    row_count: int
    col_count: int
    columns: List[ColumnSummary] = field(default_factory=list)
    preview_rows: List[Dict[str, Any]] = field(default_factory=list)


class DatasetService:
    """Parses local CSV/TSV research datasets and computes column profiles."""

    @classmethod
    def inspect_csv(cls, file_path: Path, max_preview: int = 50) -> DatasetSummary:
        """Parse CSV/TSV file, compute basic statistics, and extract preview rows."""
        path = Path(file_path).resolve()
        summary = DatasetSummary(
            file_name=path.name,
            file_path=path,
            row_count=0,
            col_count=0,
        )

        if not path.exists():
            app_logger.warning(f"Dataset '{path}' does not exist.")
            return summary

        try:
            # Detect delimiter (comma or tab)
            delimiter = "\t" if path.suffix.lower() == ".tsv" else ","

            with open(path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f, delimiter=delimiter)
                headers = next(reader, None)
                if not headers:
                    return summary

                summary.col_count = len(headers)
                col_values: Dict[str, List[Any]] = {h: [] for h in headers}

                row_idx = 0
                for row in reader:
                    if not row:
                        continue
                    row_idx += 1
                    row_dict = {}
                    for col_i, header in enumerate(headers):
                        val_str = row[col_i].strip() if col_i < len(row) else ""
                        col_values[header].append(val_str)
                        if row_idx <= max_preview:
                            row_dict[header] = val_str

                    if row_idx <= max_preview:
                        summary.preview_rows.append(row_dict)

                summary.row_count = row_idx

                # Compute column profiles
                for header in headers:
                    vals = col_values[header]
                    non_nulls = [v for v in vals if v != ""]
                    null_count = len(vals) - len(non_nulls)
                    unique_count = len(set(non_nulls))

                    # Infer dtype
                    dtype = "string"
                    min_val, max_val = None, None
                    if non_nulls:
                        # Try int
                        try:
                            int_vals = [int(v) for v in non_nulls]
                            dtype = "integer"
                            min_val = min(int_vals)
                            max_val = max(int_vals)
                        except ValueError:
                            # Try float
                            try:
                                float_vals = [float(v) for v in non_nulls]
                                dtype = "float"
                                min_val = min(float_vals)
                                max_val = max(float_vals)
                            except ValueError:
                                dtype = "string"
                                if non_nulls:
                                    min_val = min(non_nulls)
                                    max_val = max(non_nulls)

                    col_summary = ColumnSummary(
                        name=header,
                        dtype=dtype,
                        non_null_count=len(non_nulls),
                        null_count=null_count,
                        min_val=min_val,
                        max_val=max_val,
                        unique_count=unique_count,
                    )
                    summary.columns.append(col_summary)

                return summary

        except Exception as e:
            app_logger.error(f"Error inspecting dataset '{path.name}': {e}")
            return summary
