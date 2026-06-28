"""Tests for CSV and Excel parsers."""
import pytest
from app.services.csv_parser import parse_csv, count_csv_rows
from app.services.excel_parser import parse_excel, count_excel_rows


class TestCsvParser:
    def test_parse_simple_csv(self):
        content = "name,age,city\nAlice,30,Bangkok\nBob,25,Chiang Mai"
        rows = list(parse_csv(content))
        assert len(rows) == 2
        assert rows[0]["name"] == "Alice"
        assert rows[0]["age"] == "30"
        assert rows[1]["city"] == "Chiang Mai"

    def test_parse_csv_with_whitespace(self):
        content = "  name  ,  age  \n  Alice  ,  30  "
        rows = list(parse_csv(content))
        assert rows[0]["name"] == "Alice"
        assert rows[0]["age"] == "30"

    def test_count_csv_rows(self):
        content = "a,b\n1,2\n3,4\n5,6"
        assert count_csv_rows(content) == 3


class TestExcelParser:
    def test_parse_excel_basic(self):
        """Test that parse_excel handles bytes input."""
        import io
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["name", "age", "city"])
        ws.append(["Alice", "30", "Bangkok"])
        ws.append(["Bob", "25", "Chiang Mai"])

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        content = buf.read()

        rows = list(parse_excel(content))
        assert len(rows) == 2
        assert rows[0]["name"] == "Alice"
        assert rows[1]["_sheet"] == "Sheet1"

    def test_count_excel_rows(self):
        import io
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.append(["a", "b"])
        ws.append([1, 2])
        ws.append([3, 4])

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        content = buf.read()

        assert count_excel_rows(content) == 2