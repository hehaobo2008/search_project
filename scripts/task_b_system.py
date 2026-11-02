import sys

sys.stdout.reconfigure(encoding="utf-8")

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from task_b_retriever import METHODS, TaskBRetriever  # noqa: E402


class TaskBSystem:
    """端到端入口：只接收自然语言问题与方法名，不读取题型、gold 或预标条款对。"""

    def __init__(self, retriever=None):
        self.retriever = retriever or TaskBRetriever()

    def answer(self, question, method="hybrid_top7"):
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be a non-empty natural-language string")
        if method not in METHODS:
            raise ValueError("unknown method: %s" % method)
        retrieval = self.retriever.retrieve(question)
        assessment = self.retriever.assess_answerability(question)
        if assessment["decision"] == "refuse":
            return {
                "decision": "refuse",
                "method": method,
                "evidence": [],
                "diagnostics": assessment,
                "timings": retrieval["timings"],
                "max_sem": retrieval["max_sem"],
            }
        units = self.retriever.method_units(retrieval, method)
        return {
            "decision": "answer",
            "method": method,
            "evidence": units,
            "diagnostics": assessment,
            "timings": retrieval["timings"],
            "max_sem": retrieval["max_sem"],
        }

    # 以下仅用于模块测试，不参与端到端成绩
    def module_version_check(self, question):
        return self.retriever.version_check(question)

    def module_relation_check(self, pair):
        return self.retriever.inspect_relation(pair)