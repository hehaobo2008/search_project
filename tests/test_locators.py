import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from lxml import html as LH

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCATORS = os.path.join(ROOT, "locators")
REPORTS = os.path.join(ROOT, "reports")
CORPUS = os.path.join(ROOT, "corpus")

KEY_ANCHORS = {
    "rail_quality": ["art-2", "art-30", "art-66"],
    "construction_quality": ["art-29", "art-31", "art-65"],
    "rail_quality_amendment": ["decision"],
}


def norm(text):
    return " ".join(text.split())


def collect_anchor_text(root, anchor):
    positions = []
    for pos, el in enumerate(root.iter()):
        if not isinstance(el.tag, str):
            continue
        if el.get("id") == anchor or el.get("data-article-part") == anchor:
            positions.append((pos, el))
    positions.sort(key=lambda x: x[0])
    return "\n".join(norm(el.text_content()) for _, el in positions), len(
        [1 for _, el in positions if el.get("id") == anchor])


class LocatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(os.path.join(LOCATORS, "index.json")):
            subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_locators.py")],
                           cwd=ROOT, check=True, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        cls.index = json.load(open(os.path.join(LOCATORS, "index.json"), encoding="utf-8"))
        cls.articles = {(a["doc_id"], a["anchor"]): a["text"]
                        for a in [json.loads(line) for line in open(
                            os.path.join(CORPUS, "articles.jsonl"), encoding="utf-8")]}

    def test_locator_verification_passes(self):
        proc = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "verify_locators.py")],
                              cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        result = json.load(open(os.path.join(REPORTS, "locator_result.json"), encoding="utf-8"))
        self.assertGreater(result["summary"]["total"], 150)
        self.assertEqual(result["summary"]["failed"], 0)
        self.assertEqual(result["summary"]["passed"], result["summary"]["total"])

    def test_links_are_relative_not_machine_paths(self):
        for doc in self.index["documents"]:
            href = doc["local_html_href"]
            self.assertFalse(os.path.isabs(href), href)
            self.assertNotIn("file:", href)
            self.assertFalse(href[1:2] == ":" and href[0].isalpha(), href)
            self.assertTrue(os.path.exists(os.path.join(LOCATORS, href)), href)
            pdf = doc.get("pdf_href")
            if pdf:
                self.assertFalse(os.path.isabs(pdf), pdf)
                self.assertNotIn("file:", pdf)
            for anchor in doc["anchors"]:
                self.assertEqual(anchor["href"], "%s#%s" % (href, anchor["anchor"]))

    def test_locator_bundle_still_resolves_after_copy(self):
        tmp = tempfile.mkdtemp(prefix="hcs-locator-copy-")
        shutil.copytree(LOCATORS, os.path.join(tmp, "locators"))
        shutil.copytree(CORPUS, os.path.join(tmp, "corpus"))
        copied_index = json.load(open(os.path.join(tmp, "locators", "index.json"), encoding="utf-8"))
        for doc in copied_index["documents"]:
            local_path = os.path.join(tmp, "locators", doc["local_html_href"])
            self.assertTrue(os.path.exists(local_path), local_path)
            root = LH.parse(local_path).getroot()
            for anchor in KEY_ANCHORS[doc["doc_id"]]:
                actual, id_count = collect_anchor_text(root, anchor)
                self.assertEqual(id_count, 1, "%s #%s" % (doc["doc_id"], anchor))
                if anchor == "decision":
                    expected = "\n".join(line for line in open(
                        os.path.join(tmp, "corpus", "text_rail_quality_amendment.txt"),
                        encoding="utf-8").read().splitlines() if line.strip())
                else:
                    expected = self.articles[(doc["doc_id"], anchor)]
                self.assertEqual(actual, expected, "%s #%s" % (doc["doc_id"], anchor))
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()