from app import __version__
from app.gui_main import run
from app.main import main


def test_version_is_defined():
    assert __version__ == "0.1.0"


def test_main_returns_success(tmp_path, capsys):
    assert main(["--rules", str(tmp_path / "missing.json")]) == 0

    captured = capsys.readouterr()
    assert "Loaded 0 rule(s)" in captured.out


def test_main_loads_rules_from_argument(tmp_path, capsys):
    path = tmp_path / "rules.json"
    path.write_text('{"version": 1, "rules": []}', encoding="utf-8")

    assert main(["--rules", str(path)]) == 0

    captured = capsys.readouterr()
    assert "Loaded 0 rule(s)" in captured.out


def test_main_returns_failure_for_invalid_rules(tmp_path, capsys):
    path = tmp_path / "rules.json"
    path.write_text("{ invalid json", encoding="utf-8")

    assert main(["--rules", str(path)]) == 1

    captured = capsys.readouterr()
    assert "Invalid JSON" in captured.err


def test_gui_entrypoint_adds_gui_argument(monkeypatch):
    captured_args = []

    def fake_main(args):
        captured_args.extend(args)
        return 0

    monkeypatch.setattr("app.gui_main.main", fake_main)
    monkeypatch.setattr("sys.argv", ["MacroTool.exe", "--rules", "rules.json"])

    assert run() == 0
    assert captured_args == ["--rules", "rules.json", "--gui"]
