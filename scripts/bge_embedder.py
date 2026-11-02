import os
import sys

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(ROOT, "work", "models", "bge-small-zh-v1.5")
QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："


class BgeEmbedder:
    def __init__(self, model_dir=MODEL_DIR, max_length=512):
        self.max_length = max_length
        self.tokenizer = Tokenizer.from_file(os.path.join(model_dir, "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=max_length)
        self.session = ort.InferenceSession(
            os.path.join(model_dir, "onnx", "model.onnx"),
            providers=["CPUExecutionProvider"])

    def encode(self, texts, is_query=False, batch_size=8):
        if isinstance(texts, str):
            texts = [texts]
        prepared = [QUERY_INSTRUCTION + t if is_query else t for t in texts]
        encodings = self.tokenizer.encode_batch(prepared)
        vectors = []
        for start in range(0, len(encodings), batch_size):
            batch = encodings[start:start + batch_size]
            width = max(len(e.ids) for e in batch)
            input_ids = np.zeros((len(batch), width), dtype=np.int64)
            attention = np.zeros((len(batch), width), dtype=np.int64)
            type_ids = np.zeros((len(batch), width), dtype=np.int64)
            for i, enc in enumerate(batch):
                n = len(enc.ids)
                input_ids[i, :n] = enc.ids
                attention[i, :n] = enc.attention_mask
                type_ids[i, :n] = enc.type_ids
            hidden = self.session.run(None, {
                "input_ids": input_ids,
                "attention_mask": attention,
                "token_type_ids": type_ids,
            })[0]
            cls = hidden[:, 0, :].astype(np.float32)
            norms = np.linalg.norm(cls, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            vectors.append(cls / norms)
        return np.vstack(vectors)


def main():
    import json
    articles = {(a["doc_id"], a["article_num"]): a
                for a in [json.loads(line) for line in open(
                    os.path.join(ROOT, "corpus", "articles.jsonl"), encoding="utf-8")]}
    embedder = BgeEmbedder()
    query = "铁路工地试块送检要谁在场？检测记录签字的规定在哪？"
    docs = [
        ("A30", articles[("rail_quality", 30)]["text"]),
        ("A29", articles[("rail_quality", 29)]["text"]),
        ("B29", articles[("construction_quality", 29)]["text"]),
        ("B31", articles[("construction_quality", 31)]["text"]),
        ("B65", articles[("construction_quality", 65)]["text"]),
    ]
    qv = embedder.encode([query], is_query=True)[0]
    dv = embedder.encode([t for _, t in docs])
    scores = dv @ qv
    order = sorted(range(len(docs)), key=lambda i: -scores[i])
    print("query:", query)
    for i in order:
        print("%s %.4f" % (docs[i][0], scores[i]))
    top = docs[order[0]][0]
    print("top1:", top)
    sys.exit(0 if top in ("A30", "B29", "B31") else 2)


if __name__ == "__main__":
    main()