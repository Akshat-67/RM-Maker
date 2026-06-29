import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.sd.processor import coerce_roman_in_text


def test_coerce_roman_in_text_does_not_use_variable_width_lookbehind():
    assert coerce_roman_in_text("book I") == "book 01"
    assert coerce_roman_in_text("volume IV") == "volume 04"
    assert coerce_roman_in_text("No X") == "No 10"
    assert coerce_roman_in_text("Agreement I") == "Agreement I"
