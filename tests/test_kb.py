from licensewise import kb


def test_copyleft_levels():
    lics = kb.licenses()
    assert kb.copyleft(lics["GPL-3.0"]) == "whole_work"
    assert kb.copyleft(lics["AGPL-3.0"]) == "whole_work"
    assert kb.copyleft(lics["LGPL-3.0"]) == "file_or_library"
    assert kb.copyleft(lics["MPL-2.0"]) == "file_or_library"
    assert kb.copyleft(lics["MIT"]) == "none"


def test_kb_id_strips_spdx_suffixes():
    assert kb.kb_id("GPL-3.0-or-later") == "GPL-3.0"
    assert kb.kb_id("LGPL-2.1-only") == "LGPL-2.1"
    assert kb.kb_id("MIT") == "MIT"
    assert kb.kb_id("Not-A-License") is None
    assert kb.kb_id(None) is None


def test_catalogue_v1_has_no_labels_and_v2_does():
    v1, v2 = kb.catalogue(), kb.catalogue(labels=True)
    assert "[permissions:" not in v1
    assert len(v1.splitlines()) == len(v2.splitlines()) == len(kb.licenses())
    apache = next(line for line in v2.splitlines() if line.startswith("- Apache-2.0:"))
    assert "trademark-use" in apache and "document-changes" in apache
