"""
db.sqlalchemy.migrate 模块测试 — 迁移 CLI 与工具函数
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastapi_augment.db.sqlalchemy.migrate import (
    init_project,
    _resolve_alembic_config,
    cli_main,
)


# ── init_project ──────────────────────────────────────────────────────

class TestInitProject:

    def test_creates_alembic_ini(self, tmp_path: Path):
        init_project('sqlite:///test.db', project_dir=tmp_path)
        ini = tmp_path / 'alembic.ini'
        assert ini.exists()
        content = ini.read_text()
        assert 'sqlite:///test.db' in content
        assert 'script_location' in content

    def test_creates_versions_dir(self, tmp_path: Path):
        init_project('sqlite:///test.db', project_dir=tmp_path)
        versions = tmp_path / 'migrations' / 'versions'
        assert versions.is_dir()

    def test_does_not_overwrite_existing_ini(self, tmp_path: Path):
        ini = tmp_path / 'alembic.ini'
        ini.write_text('# original content')
        init_project('sqlite:///other.db', project_dir=tmp_path)
        assert ini.read_text() == '# original content'

    def test_custom_db_url_in_ini(self, tmp_path: Path):
        init_project('postgresql+asyncpg://user:pass@host/db', project_dir=tmp_path)
        content = (tmp_path / 'alembic.ini').read_text()
        assert 'postgresql+asyncpg://user:pass@host/db' in content


# ── _resolve_alembic_config ───────────────────────────────────────────

class TestResolveAlembicConfig:

    def test_missing_ini_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError, match='请先执行'):
            _resolve_alembic_config(project_dir=tmp_path)

    def test_with_existing_ini(self, tmp_path: Path):
        init_project('sqlite:///test.db', project_dir=tmp_path)
        cfg = _resolve_alembic_config(project_dir=tmp_path)
        assert cfg.get_main_option('sqlalchemy.url') == 'sqlite:///test.db'

    def test_db_url_override(self, tmp_path: Path):
        init_project('sqlite:///test.db', project_dir=tmp_path)
        cfg = _resolve_alembic_config(db_url='sqlite:///override.db', project_dir=tmp_path)
        assert cfg.get_main_option('sqlalchemy.url') == 'sqlite:///override.db'


# ── cli_main ──────────────────────────────────────────────────────────

class TestCliMain:

    def test_init_command(self, tmp_path: Path):
        with patch('sys.argv', ['migrate', 'init', '--db-url', 'sqlite:///cli.db', '--project-dir', str(tmp_path)]):
            cli_main()
        assert (tmp_path / 'alembic.ini').exists()

    def test_upgrade_without_ini_exits(self, tmp_path: Path):
        with patch('sys.argv', ['migrate', 'upgrade', '--project-dir', str(tmp_path)]):
            with pytest.raises(SystemExit):
                cli_main()

    def test_generate_without_ini_exits(self, tmp_path: Path):
        with patch('sys.argv', ['migrate', 'generate', '--message', 'test', '--models', 'models', '--project-dir', str(tmp_path)]):
            with pytest.raises(SystemExit):
                cli_main()
