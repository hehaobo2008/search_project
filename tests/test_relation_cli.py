import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "build_relations.py")


def article(doc_id, version, num, text):
    return {
        "doc_id": doc_id,
        "version_id": version,
        "article_id": "%s:art-%d" % (doc_id, num),
        "article_no": "第%d条" % num,
        "article_num": num,
        "text": text,
        "start": 0,
        "end": len(text),
    }


def make_corpus(tmp, b_order):
    corpus = os.path.join(tmp, "corpus")
    os.makedirs(corpus, exist_ok=True)
    b_docs = {
        "revised_2019_04_23": {"doc_id": "construction_quality", "version_id": "revised_2019_04_23"},
        "revised_2017_10_07": {"doc_id": "construction_quality", "version_id": "revised_2017_10_07"},
    }
    docs = [
        {"doc_id": "rail_quality", "version_id": "amended_2021_12_23"},
        b_docs[b_order[0]],
        b_docs[b_order[1]],
        {"doc_id": "rail_quality_amendment", "version_id": "2021_order_35"},
    ]
    with open(os.path.join(corpus, "docs_manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"documents": docs}, f, ensure_ascii=False, indent=2)
    arts = [
        article("rail_quality", "amended_2021_12_23", 1,
                "第一条 依据《建设工程质量管理条例》第六十五条规定制定。"),
        article("construction_quality", "revised_2019_04_23", 65, "第六十五条 2019版责任文字。"),
        article("construction_quality", "revised_2017_10_07", 65, "第六十五条 2017版责任文字。"),
    ]
    with open(os.path.join(corpus, "articles.jsonl"), "w", encoding="utf-8") as f:
        for art in arts:
            f.write(json.dumps(art, ensure_ascii=False) + "\n")
    with open(os.path.join(corpus, "text_rail_quality_amendment.txt"), "w", encoding="utf-8") as f:
        f.write("本决定自公布之日起施行。")
    return corpus


def run_cli(corpus, pins_path):
    env = os.environ.copy()
    env["HCS_CORPUS_DIR"] = corpus
    env["HCS_VERSION_PINS"] = pins_path
    proc = subprocess.run([sys.executable, SCRIPT], cwd=ROOT, env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    rel_path = os.path.join(corpus, "relations.jsonl")
    rels = [json.loads(line) for line in open(rel_path, encoding="utf-8")] if os.path.exists(rel_path) else []
    diag_path = os.path.join(corpus, "relation_diagnostics.json")
    diag = json.load(open(diag_path, encoding="utf-8")) if os.path.exists(diag_path) else {}
    return proc, rels, diag


class RelationCliTest(unittest.TestCase):
    def _target_edge(self, rels):
        return next(r for r in rels
                    if r["source"]["article_id"] == "rail_quality:art-1"
                    and r["relation_type"] in ("explicit_article", "explicit_document"))

    def test_missing_config_with_two_versions_stops_regardless_of_order(self):
        for order in (["revised_2019_04_23", "revised_2017_10_07"],
                      ["revised_2017_10_07", "revised_2019_04_23"]):
            with self.subTest(order=order):
                tmp = tempfile.mkdtemp(prefix="hcs-cli-")
                corpus = make_corpus(tmp, order)
                proc, rels, diag = run_cli(corpus, os.path.join(tmp, "no_pins.json"))
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                edge = self._target_edge(rels)
                self.assertIsNone(edge["target"])
                self.assertEqual(edge["target_version_status"], "ambiguous_version")
                self.assertTrue(any(d["target_version_status"] == "ambiguous_version"
                                    for d in diag["diagnostics"]))
                self.assertEqual(diag["pinned_versions"], {})
                shutil.rmtree(tmp, ignore_errors=True)

    def test_explicit_pin_selects_2019_regardless_of_order(self):
        for order in (["revised_2019_04_23", "revised_2017_10_07"],
                      ["revised_2017_10_07", "revised_2019_04_23"]):
            with self.subTest(order=order):
                tmp = tempfile.mkdtemp(prefix="hcs-cli-")
                corpus = make_corpus(tmp, order)
                pins_path = os.path.join(tmp, "pins.json")
                with open(pins_path, "w", encoding="utf-8") as f:
                    json.dump({"schema_version": 1, "pins": {
                        "rail_quality": "amended_2021_12_23",
                        "construction_quality": "revised_2019_04_23",
                        "rail_quality_amendment": "2021_order_35",
                    }}, f, ensure_ascii=False)
                proc, rels, diag = run_cli(corpus, pins_path)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                edge = self._target_edge(rels)
                self.assertIsNotNone(edge["target"])
                self.assertEqual(edge["target"]["version_id"], "revised_2019_04_23")
                self.assertEqual(edge["target_version_status"], "resolved")
                self.assertEqual(diag["pinned_versions"]["construction_quality"],
                                 "revised_2019_04_23")
                shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()