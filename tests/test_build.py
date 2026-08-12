import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build import inline, render_body


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

    def test_plain_project_hashes_become_direct_github_links(self):
        rendered = inline("（poly-terminal：abcdef12、1234567；polybot：89abcdef）")

        self.assertIn('href="https://github.com/HQSV-Labs/poly-terminal/commit/abcdef12"', rendered)
        self.assertIn('href="https://github.com/HQSV-Labs/poly-terminal/commit/1234567"', rendered)
        self.assertIn('href="https://github.com/HQSV-Labs/polybot/commit/89abcdef"', rendered)

    def test_existing_full_commit_link_is_not_wrapped_again(self):
        rendered = inline(
            "（polybot：[abcdef12](https://github.com/HQSV-Labs/polybot/commit/abcdef1234567890abcdef1234567890abcdef12)）"
        )

        self.assertEqual(rendered.count("<a href="), 1)

    def test_hash_outside_project_reference_stays_plain(self):
        self.assertEqual(inline("版本 abcdef12"), "版本 abcdef12")


if __name__ == "__main__":
    unittest.main()
