import io
from prototype.prototype import write_srt


def test_write_srt_basic(tmp_path):
    segments = [
        {"start": 0.0, "end": 1.5, "text": "Hello world"},
        {"start": 2.0, "end": 4.123, "text": "Second line"},
    ]
    p = tmp_path / "out.srt"
    write_srt(segments, p)
    content = p.read_text(encoding='utf-8')
    assert "00:00:00,000 --> 00:00:01,500" in content
    assert "Hello world" in content
    assert "00:00:02,000 --> 00:00:04,123" in content
    assert "Second line" in content
