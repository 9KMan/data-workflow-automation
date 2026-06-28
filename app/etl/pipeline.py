"""ETL pipeline orchestration."""
import logging
import time
from datetime import datetime
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.config import settings
from app.models import PipelineRun, PipelineStatus, TransformationRule

log = logging.getLogger(__name__)


class ETLPipeline:
    """Configurable ETL pipeline that reads transformation rules from DB."""

    def __init__(self, pipeline_name: str, db: Session):
        self.pipeline_name = pipeline_name
        self.db = db
        self.max_retries = settings.ETL_MAX_RETRIES
        self.batch_size = settings.ETL_BATCH_SIZE
        self._run: PipelineRun | None = None

    def _get_rules(self, source_table: str) -> list[TransformationRule]:
        return (
            self.db.query(TransformationRule)
            .filter(TransformationRule.source_table == source_table)
            .all()
        )

    def _apply_transform(
        self, row: dict, rules: list[TransformationRule]
    ) -> dict:
        """Apply all transformation rules to a single row dict."""
        result = dict(row)
        for rule in rules:
            if rule.transform_type == "drop":
                result.pop(rule.field_name, None)
            elif rule.transform_type == "coerce":
                cfg = rule.transform_config or {}
                if rule.field_name in result:
                    t = cfg.get("type", "str")
                    default = cfg.get("default")
                    try:
                        if t == "int":
                            result[rule.field_name] = int(result[rule.field_name])
                        elif t == "float":
                            result[rule.field_name] = float(result[rule.field_name])
                        elif t == "bool":
                            result[rule.field_name] = bool(result[rule.field_name])
                        # else keep as-is
                    except (ValueError, TypeError):
                        result[rule.field_name] = default
            elif rule.transform_type == "default":
                cfg = rule.transform_config or {}
                if rule.field_name not in result or result[rule.field_name] is None:
                    result[rule.field_name] = cfg.get("default")
            elif rule.transform_type == "map":
                cfg = rule.transform_config or {}
                if rule.field_name in result:
                    mapping = cfg.get("map", {})
                    result[rule.field_name] = mapping.get(
                        result[rule.field_name], result[rule.field_name]
                    )
            # custom: caller registers a hook via registry
        return result

    def run(
        self,
        source_table: str,
        target_table: str,
        rows: list[dict],
        custom_transforms: dict[str, Callable] | None = None,
    ) -> tuple[int, int]:
        """
        Run ETL on a batch of rows.
        Returns (rows_processed, rows_failed).
        """
        # Log pipeline run start
        self._run = PipelineRun(
            pipeline_name=self.pipeline_name,
            status=PipelineStatus.RUNNING.value,
        )
        self.db.add(self._run)
        self.db.commit()
        self.db.refresh(self._run)

        rules = self._get_rules(source_table)
        processed = 0
        failed = 0
        errors = []

        for i, row in enumerate(rows):
            for attempt in range(self.max_retries):
                try:
                    # Apply standard transforms
                    transformed = self._apply_transform(row, rules)

                    # Apply custom transforms
                    if custom_transforms:
                        for field, fn in custom_transforms.items():
                            if field in transformed:
                                transformed[field] = fn(transformed[field])

                    # Store to processed data (simplified — write to target)
                    # In production this would be a bulk insert; kept simple for demo
                    processed += 1
                    break
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        failed += 1
                        errors.append(f"Row {i}: {e}")
                    else:
                        time.sleep(0.1 * (2 ** attempt))

        # Finalize run
        self._run.rows_processed = processed
        self._run.rows_failed = failed
        self._run.status = (
            PipelineStatus.DONE.value if failed == 0 else PipelineStatus.FAILED.value
        )
        self._run.finished_at = datetime.utcnow()
        if errors:
            self._run.error_message = "; ".join(errors[:10])  # cap at 10 errors
        self.db.commit()

        log.info(
            f"Pipeline {self.pipeline_name}: {processed} processed, {failed} failed"
        )
        return processed, failed