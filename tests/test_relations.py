import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(ROOT, "corpus")


class RelationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.relations = [json.loads(line) for line in open(
            os.path.join(CORPUS, "relations.jsonl"), encoding="utf-8")]

    def test_a66_to_b65_is_article_level_2019(self):
        edges = [r for r in self.relations
                 if r["source"]["article_id"] == "rail_quality:art-66"
                 and r["relation_type"] == "explicit_article"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["target"]["article_no"], "第六十五条")
        self.assertEqual(edges[0]["target"]["version_id"], "revised_2019_04_23")
        self.assertEqual(edges[0]["target_version_status"], "resolved")

    def test_a30_has_no_explicit_edge_to_b29_b31(self):
        bad = [r for r in self.relations
               if r["source"]["article_id"] == "rail_quality:art-30"
               and r["relation_type"].startswith("explicit")
               and r["target"] and r["target"]["doc_id"] == "construction_quality"]
        self.assertEqual(bad, [])
        topic = [r for r in self.relations
                 if r["source"]["article_id"] == "rail_quality:art-30"
                 and r["relation_type"] == "topic_related"]
        self.assertEqual(len(topic), 2)
        self.assertTrue(all(r["target_version_status"] == "resolved" for r in topic))

    def test_a1_to_b_is_document_level_only(self):
        a1 = [r for r in self.relations if r["source"]["article_id"] == "rail_quality:art-1"]
        b_doc = [r for r in a1 if r["relation_type"] == "explicit_document"
                 and r["target"] is None and "建设工程质量管理条例" in r["evidence_text"]]
        a1_articles = [r for r in a1 if r["relation_type"] == "explicit_article"]
        self.assertEqual(len(b_doc), 1)
        self.assertEqual(b_doc[0]["target_version_status"], "pinned")
        self.assertEqual(a1_articles, [])

    def test_no_ambiguous_target_versions(self):
        ambiguous = [r for r in self.relations
                     if r["target_version_status"] in ("ambiguous_version", "pinned_version_missing")]
        self.assertEqual(ambiguous, [])


if __name__ == "__main__":
    unittest.main()