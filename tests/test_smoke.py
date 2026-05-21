"""Smoke tests for the RecruiTree V2 package scaffold."""

from importlib import import_module


def test_v2_scaffold_modules_are_importable() -> None:
    """The top-level app and package namespaces should import cleanly."""
    modules = [
        "app.main",
        "app.ui",
        "recruitree",
        "recruitree.core",
        "recruitree.ingest",
        "recruitree.llm",
        "recruitree.llm.prompts",
        "recruitree.generate",
        "recruitree.review",
        "recruitree.publish",
    ]

    for module in modules:
        assert import_module(module)
