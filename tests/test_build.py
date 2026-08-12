import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build import render_body


class RenderBodyTests(unittest.TestCase):
    def test_blank_lines_do_not_restart_ordered_list(self):
        rendered = render_body(("", "1. 第一项", "", "2. 第二项", "", "3. 第三项"))

        self.assertEqual(rendered.count("<ol>"), 1)
        self.assertEqual(rendered.count("</ol>"), 1)
        self.assertEqual(rendered.count("<li>"), 3)

    def test_section_heading_starts_a_new_ordered_list(self):
        rendered = render_body(("【前端】", "1. 第一项", "", "2. 第二项", "", "【后端】", "3. 第三项"))

        self.assertEqual(rendered.count("<ol>"), 2)
        self.assertIn("</ol>\n<h3>后端</h3>\n<ol>", rendered)


if __name__ == "__main__":
    unittest.main()
