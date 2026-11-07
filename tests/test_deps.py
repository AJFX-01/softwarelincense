import json

import pytest

from licensewise import deps


def test_parse_package_json(tmp_path):
    path = tmp_path / "package.json"
    path.write_text(json.dumps({"dependencies": {"react": "^19", "lodash": "4"},
                                "devDependencies": {"vite": "8"}}))
    assert deps.parse_manifest(path) == ("npm", ["lodash", "react"])


def test_parse_requirements_txt_skips_options_urls_and_comments(tmp_path):
    path = tmp_path / "requirements.txt"
    path.write_text("Flask>=3  # web\n-r other.txt\ngit+https://x/y.git\n\nnumpy==2.0\nflask\n")
    assert deps.parse_manifest(path) == ("pypi", ["flask", "numpy"])


def test_parse_pyproject(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\nname = "x"\ndependencies = ["requests>=2", "PyYAML"]\n')
    assert deps.parse_manifest(path) == ("pypi", ["pyyaml", "requests"])


def test_unsupported_manifest(tmp_path):
    path = tmp_path / "Cargo.toml"
    path.write_text("")
    with pytest.raises(ValueError):
        deps.parse_manifest(path)


@pytest.mark.parametrize("raw, expected", [
    ("MIT", "MIT"),
    ("License :: OSI Approved :: MIT License", "MIT"),
    ("MIT OR Apache-2.0", "MIT OR Apache-2.0"),
    ("", None),
    ("x" * 200, None),  # full license text pasted into the field
])
def test_normalize(raw, expected):
    assert deps.normalize(raw) == expected
