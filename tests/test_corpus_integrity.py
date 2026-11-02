import hashlib
import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, "corpus")


class CorpusIntegrityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.articles = [json.loads(line) for line in open(
            os.path.join(CORPUS, "articles.jsonl"), encoding="utf-8")]
        cls.manifest = json.load(open(os.path.join(CORPUS, "docs_manifest.json"), encoding="utf-8"))

    def test_article_numbers_contiguous(self):
        a = sorted(x["article_num"] for x in self.articles if x["doc_id"] == "rail_quality")
        b = sorted(x["article_num"] for x in self.articles if x["doc_id"] == "construction_quality")
        self.assertEqual(a, list(range(1, 76)))
        self.assertEqual(b, list(range(1, 83)))

    def test_span_and_hash(self):
        for art in self.articles:
            self.assertTrue(art["span_check"], art["article_id"])
            self.assertEqual(art["sha256"],
                             hashlib.sha256(art["text"].encode("utf-8")).hexdigest(),
                             art["article_id"])

    def test_b31_corrected_to_page_7_with_legacy_record(self):
        b31 = next(x for x in self.articles
                   if x["doc_id"] == "construction_quality" and x["article_num"] == 31)
        self.assertEqual(b31["pdf_page_start"], 7)
        self.assertFalse(b31["pdf_cross_page"])
        self.assertEqual(b31["page_record_correction"]["status"], "corrected")
        b_doc = next(d for d in self.manifest["documents"] if d["doc_id"] == "construction_quality")
        legacy = [r for r in b_doc["legacy_records"] if r["record_id"] == "B31-page"]
        self.assertEqual(len(legacy), 1)
        self.assertEqual(legacy[0]["status"], "superseded")
        self.assertIn("续至第8页", legacy[0]["record"])


if __name__ == "__main__":
    unittest.main()