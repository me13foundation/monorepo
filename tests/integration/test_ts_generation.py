from __future__ import annotations

import importlib
import sys

import pytest


@pytest.fixture
def generator_module():
    return importlib.import_module("scripts.generate_ts_types")


def test_type_generation_writes_interfaces(
    tmp_path,
    monkeypatch,
    generator_module,
) -> None:
    output_path = tmp_path / "types.ts"
    monkeypatch.setattr(generator_module, "OUTPUT_PATH", output_path)
    monkeypatch.setattr(sys, "argv", ["generate_ts_types"])

    generator_module.main()

    assert output_path.exists(), "Type generation should create the output file"
    contents = output_path.read_text(encoding="utf-8")
    assert "export interface GeneResponse" in contents
    assert "export interface VariantResponse" in contents
