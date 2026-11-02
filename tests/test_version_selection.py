import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from build_relations import extract_relations  # noqa: E402


def make_article(doc_id, version_id, num, text):
    return {
        "doc_id": doc_id,
        "version_id": version_id,
        "article_id": "%s:art-%d" % (doc_id, num),
        "article_no": "第%d条" % num,
        "article_num": num,
        "text": text,
        "start": 0,
        "end": len(text),
    }


class VersionSelectionTest(unittest.TestCase):
    def setUp(self):
        self.articles = [
            make_article("rail_quality", "amended_2021_12_23", 1,
                         "第一条 依据《建设工程质量管理条例》第六十五条规定制定。"),
            make_article("construction_quality", "revised_2019_04_23", 65, "第六十五条 2019版责任文字。"),
            make_article("construction_quality", "revised_2017_10_07", 65, "第六十五条 2017版责任文字。"),
        ]
        self.docs = [
            {"doc_id": "rail_quality", "version_id": "amended_2021_12_23"},
            {"doc_id": "construction_quality", "version_id": "revised_2019_04_23"},
            {"doc_id": "construction_quality", "version_id": "revised_2017_10_07"},
        ]

    def test_unpinned_multi_version_is_ambiguous_and_blocks_edge(self):
        relations, diagnostics = extract_relations(self.articles, self.docs, "", {})
        edge = next(r for r in relations if r["source"]["article_id"] == "rail_quality:art-1")
        self.assertIsNone(edge["target"])
        self.assertEqual(edge["target_version_status"], "ambiguous_version")
        self.assertTrue(any(d["target_version_status"] == "ambiguous_version" for d in diagnostics))

    def test_pinned_version_selects_2019_only(self):
        relations, _ = extract_relations(
            self.articles, self.docs, "",
            {"rail_quality": "amended_2021_12_23", "construction_quality": "revised_2019_04_23"})
        edges = [r for r in relations
                 if r["source"]["article_id"] == "rail_quality:art-1"
                 and r["relation_type"] == "explicit_article"]
        self.assertEqual(len(edges), 1)
        self.assertIsNotNone(edges[0]["target"])
        self.assertEqual(edges[0]["target"]["version_id"], "revised_2019_04_23")

    def test_pinned_missing_version_pends_not_guesses(self):
        relations, _ = extract_relations(
            self.articles, self.docs, "",
            {"rail_quality": "amended_2021_12_23", "construction_quality": "revised_2020_01_01"})
        edge = next(r for r in relations if r["source"]["article_id"] == "rail_quality:art-1")
        self.assertIsNone(edge["target"])
        self.assertEqual(edge["target_version_status"], "pinned_version_missing")


if __name__ == "__main__":
    unittest.main()