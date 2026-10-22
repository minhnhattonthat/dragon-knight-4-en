import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
import layout  # noqa: E402


def test_wrap_after_inline_number():
    # text after an inline number keeps its own leading space, or attaches with none
    assert layout.wrap(' lying here.', 10, first_indent=' ')[0] == ' lying here.'
    assert layout.wrap('!!', 10, first_indent='')[0] == '!!'
    # no room left on the number's line: the first line is empty and the text starts on the next
    assert layout.wrap(' lying here.', 1, first_indent=' ') == [' ', ' lying here.']
