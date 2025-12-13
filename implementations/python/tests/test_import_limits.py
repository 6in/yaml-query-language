"""Tests for import limits and circular dependency detection."""

from pathlib import Path

import pytest

from yql import parse_file
from yql.parser import ParseError

FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"


class TestCircularDependency:
    """Tests for circular dependency detection."""
    
    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected."""
        with pytest.raises(ParseError) as exc_info:
            parse_file(FIXTURES_DIR / "test_circular_import_a" / "before.yql")
        
        error = exc_info.value
        assert error.category == "logic_error"
        assert "Circular dependency" in error.message
        assert "circular_path" in error.details


class TestImportDepthLimit:
    """Tests for import depth limit."""
    
    def test_import_depth_exceeds_limit(self):
        """Test that import depth limit is enforced."""
        # level1 -> level2 -> level3 -> level4
        # With max_depth=2, depth 0->1->2->3 should fail at depth 3
        # level3 (depth=2) が level4 (depth=3) をimportしようとする時、エラーになるはず
        from yql.parser import _load_imports
        import yaml
        
        # level3を直接ロードして、そのimportsを処理する
        level3_path = FIXTURES_DIR / "test_deep_import_level3" / "before.yql"
        content = level3_path.read_text()
        data = yaml.safe_load(content)
        
        # level3のimportsを処理する（depth=2, max_depth=2）
        # level3がlevel4をimportしようとする時、depth=3になるのでエラーになるはず
        with pytest.raises(ParseError) as exc_info:
            imports = data.get("imports", [])
            # level3ファイルを読み込んで、その中でlevel4をimportしようとする
            # この時、depth=2からdepth=3になるので、max_depth=2ならエラーになる
            _load_imports(imports, level3_path.parent, current_file=level3_path, depth=2, max_depth=2)
        
        error = exc_info.value
        assert error.category == "logic_error"
        assert "Import depth exceeds maximum" in error.message
        assert error.details["max_depth"] == 2
        assert error.details["depth"] == 2  # depth=2でlevel4をimportしようとする前にチェックが実行される


class TestImportCountLimit:
    """Tests for import count limit."""
    
    def test_too_many_imports(self):
        """Test that import count limit is enforced."""
        # Create a YQL file with too many imports
        yql_content = """
imports:
"""
        for i in range(11):
            yql_content += f'  - "test_import_customer_summary"\n'
        
        yql_content += """
query:
  select:
    - id: c.id
  from: { c: customers }
"""
        
        with pytest.raises(ParseError) as exc_info:
            from yql.parser import parse
            parse(yql_content)
        
        error = exc_info.value
        assert error.category == "logic_error"
        assert "Too many imports" in error.message
        assert error.details["import_count"] == 11

