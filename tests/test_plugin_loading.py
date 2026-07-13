"""Plugin loading tests."""

from __future__ import annotations

import sys
from textwrap import dedent

import pytest

from conftest import require_qt
from vegas_doc.plugins.loader import PluginLoader
from vegas_doc.plugins.manager import PluginManager
from vegas_doc.plugins.plugin import Plugin, PluginMetadata
from vegas_doc.plugins.registry import PluginRegistry


class DummyPlugin(Plugin):
    """Minimal non-Qt plugin for registry tests."""

    def __init__(self, plugin_id: str, order: int = 100) -> None:
        self.metadata = PluginMetadata(plugin_id, plugin_id.title(), "test", order)

    def create_widget(self, context):  # type: ignore[no-untyped-def]
        """Return a non-Qt placeholder for architecture tests."""

        return object()


def test_registry_rejects_duplicate_plugin_ids() -> None:
    """Duplicate plugin IDs are rejected at registration time."""

    registry = PluginRegistry()
    registry.register(DummyPlugin("duplicate"))

    with pytest.raises(ValueError, match="Duplicate plugin ID"):
        registry.register(DummyPlugin("duplicate"))


def test_loader_isolates_broken_plugins(tmp_path) -> None:
    """A broken plugin module does not prevent healthy plugins from loading."""

    package = tmp_path / "fake_plugins"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "healthy.py").write_text(
        dedent(
            """
            from vegas_doc.plugins.plugin import Plugin, PluginMetadata

            class HealthyPlugin(Plugin):
                def __init__(self):
                    self.metadata = PluginMetadata('healthy', 'Healthy', 'ok', 1)

                def create_widget(self, context):
                    return object()

            def create_plugin():
                return HealthyPlugin()
            """
        ),
        encoding="utf-8",
    )
    (package / "broken.py").write_text("def create_plugin():\n    raise RuntimeError('boom')\n", encoding="utf-8")
    sys.path.insert(0, str(tmp_path))
    try:
        result = PluginLoader("fake_plugins").load()
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("fake_plugins", None)
        sys.modules.pop("fake_plugins.healthy", None)
        sys.modules.pop("fake_plugins.broken", None)

    assert [plugin.metadata.plugin_id for plugin in result.plugins] == ["healthy"]
    assert len(result.errors) == 1
    assert "boom" in result.errors[0].message


def test_builtin_plugins_load_in_navigation_order(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Built-in placeholder modules are discovered without MainWindow changes."""

    require_qt()
    from vegas_doc.config.defaults import AppSettings
    from vegas_doc.core.application_context import build_application_context

    context = build_application_context(AppSettings(), data_dir=tmp_path)
    plugins = PluginManager(PluginLoader(context.settings.plugins_package)).load_installed()

    assert [plugin.metadata.name for plugin in plugins] == [
        "Manual Generator",
        "DQ Generator",
        "F&DS Generator",
        "Settings",
    ]
