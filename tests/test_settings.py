"""
config.settings 模块测试 — EnvSettings.from_env() 配置管理
"""
import os
import pytest
from fastapi_augment.config.settings import EnvSettings


# ── 测试用配置类 ──────────────────────────────────────────────────────

class AppConfig(EnvSettings):
    database_url: str = 'sqlite:///default.db'
    debug: bool = False
    secret_key: str = 'change-me'


# ── Tests ─────────────────────────────────────────────────────────────

class TestEnvSettings:

    def test_default_values(self):
        cfg = AppConfig()
        assert cfg.database_url == 'sqlite:///default.db'
        assert cfg.debug is False
        assert cfg.secret_key == 'change-me'

    def test_from_env_field_overrides(self):
        cfg = AppConfig.from_env(debug=True, secret_key='my-secret')
        assert cfg.debug is True
        assert cfg.secret_key == 'my-secret'
        # 未覆盖的字段保持默认
        assert cfg.database_url == 'sqlite:///default.db'

    def test_from_env_extra_ignore(self):
        """extra='ignore' — 未声明的字段被安全忽略"""
        cfg = AppConfig.from_env(nonexistent_field='ignored')
        assert cfg.database_url == 'sqlite:///default.db'

    def test_from_env_with_env_prefix(self, monkeypatch: pytest.MonkeyPatch):
        """env_prefix 过滤环境变量"""
        monkeypatch.setenv('MYAPP_DATABASE_URL', 'postgresql://prod/db')
        monkeypatch.setenv('MYAPP_DEBUG', 'true')

        cfg = AppConfig.from_env(env_prefix='MYAPP_')
        assert cfg.database_url == 'postgresql://prod/db'
        assert cfg.debug is True

    def test_from_env_config_vs_field_separation(self):
        """SettingsConfigDict 参数和模型字段值被正确区分"""
        cfg = AppConfig.from_env(
            env_prefix='TEST_',       # → SettingsConfigDict
            debug=True,               # → 模型字段值
        )
        assert cfg.debug is True
        # model_config 被覆盖为带前缀
        assert cfg.model_config.get('env_prefix') == 'TEST_'

    def test_from_env_returns_correct_type(self):
        cfg = AppConfig.from_env(debug=True)
        assert isinstance(cfg, AppConfig)

    def test_env_override_beats_default(self, monkeypatch: pytest.MonkeyPatch):
        """环境变量优先级高于默认值"""
        monkeypatch.setenv('DATABASE_URL', 'postgresql://env/db')
        cfg = AppConfig()
        assert cfg.database_url == 'postgresql://env/db'


class TestEnvSettingsWithEnvFile:

    def test_from_env_with_env_file(self, tmp_path):
        """from_env 加载 .env 文件"""
        env_file = tmp_path / '.env'
        env_file.write_text('DATABASE_URL=sqlite:///from_file.db\nDEBUG=true\n')

        cfg = AppConfig.from_env(env_file=str(env_file))
        assert cfg.database_url == 'sqlite:///from_file.db'
        assert cfg.debug is True
