"""Tests for ETL pipeline."""
import pytest
from app.etl.pipeline import ETLPipeline
from app.models import TransformationRule, PipelineRun


class TestETLPipeline:
    def test_apply_coerce_int(self, test_db):
        rule = TransformationRule(
            source_table="raw",
            target_table="processed",
            field_name="age",
            transform_type="coerce",
            transform_config={"type": "int", "default": 0},
        )
        test_db.add(rule)
        test_db.commit()

        pipeline = ETLPipeline("test_pipeline", test_db)
        row = {"name": "Alice", "age": "30"}
        result = pipeline._apply_transform(row, [rule])
        assert result["age"] == 30
        assert result["name"] == "Alice"  # unchanged

    def test_apply_drop_field(self, test_db):
        rule = TransformationRule(
            source_table="raw",
            target_table="processed",
            field_name="temp_col",
            transform_type="drop",
        )
        test_db.add(rule)
        test_db.commit()

        pipeline = ETLPipeline("test_pipeline", test_db)
        row = {"name": "Alice", "temp_col": "delete me"}
        result = pipeline._apply_transform(row, [rule])
        assert "temp_col" not in result
        assert "name" in result

    def test_apply_default(self, test_db):
        rule = TransformationRule(
            source_table="raw",
            target_table="processed",
            field_name="status",
            transform_type="default",
            transform_config={"default": "pending"},
        )
        test_db.add(rule)
        test_db.commit()

        pipeline = ETLPipeline("test_pipeline", test_db)

        # None value gets default
        row = {"name": "Alice", "status": None}
        result = pipeline._apply_transform(row, [rule])
        assert result["status"] == "pending"

        # Existing value kept
        row2 = {"name": "Bob", "status": "done"}
        result2 = pipeline._apply_transform(row2, [rule])
        assert result2["status"] == "done"

    def test_run_pipeline(self, test_db):
        pipeline = ETLPipeline("test_run", test_db)
        rows = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]
        processed, failed = pipeline.run("raw", "processed", rows)
        assert processed == 2
        assert failed == 0

        # Check pipeline run was logged
        run = test_db.query(PipelineRun).filter(
            PipelineRun.pipeline_name == "test_run"
        ).first()
        assert run is not None
        assert run.status == "done"