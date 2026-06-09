"""
memcon_capture must keep the FULL raw text on disk (it's the documented source of
truth) — locks the fix for the silent 16k truncation. Pure helper, no stack.
"""
from memory.capture import _raw_for_disk, _RAW_CAP


def test_raw_for_disk_preserves_a_long_transcript_verbatim():
    # ~50k chars — well past the old 16k cap, well under the new generous ceiling.
    t = ("claude > why are requests failing under burst load again?\n"
         "the fix was raising the pool to 50 and moving the lua script off the hot path.\n") * 350
    assert len(t) > 16_000
    assert _raw_for_disk(t) == t          # nothing dropped — the old bug is gone


def test_raw_for_disk_marks_truncation_instead_of_silently_dropping():
    t = "x" * (_RAW_CAP + 5_000)
    out = _raw_for_disk(t)
    assert out.startswith("x" * 1_000)
    assert "truncated 5,000 chars" in out  # visible marker, never a silent cut
    assert len(out) >= _RAW_CAP


def test_raw_for_disk_handles_empty_and_none():
    assert _raw_for_disk("") == ""
    assert _raw_for_disk(None) == ""
