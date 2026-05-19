from typing import List
from pydantic import BaseModel
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()


class EvalResult(BaseModel):
    score: int           # 1-5
    faithful: bool       # is the answer grounded in the context?
    relevant: bool       # does it address the question?
    reason: str          # one-line explanation


class EvalSummary(BaseModel):
    results: List[EvalResult]
    average_score: float
    faithfulness_rate: float  # % of answers that are faithful
    relevance_rate: float


def evaluate_answer(question: str, context: str, answer: str) -> EvalResult:
    prompt = f"""You are evaluating a RAG system. Given the question, the retrieved context, and the generated answer, score the answer.

Question: {question}

Retrieved Context:
{context}

Generated Answer:
{answer}

Evaluate:
- score: 1 (terrible) to 5 (perfect)
- faithful: true if the answer is grounded in the context, false if it contains hallucinations
- relevant: true if the answer addresses the question
- reason: one sentence explaining your score"""

    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
        output_format=EvalResult,
    )
    return response.parsed_output


def run_eval(test_cases: list[dict]) -> EvalSummary:
    results = []
    for i, case in enumerate(test_cases):
        print(f"Evaluating {i + 1}/{len(test_cases)}: {case['question'][:50]}...")
        result = evaluate_answer(case["question"], case["context"], case["answer"])
        results.append(result)
        print(f"  Score: {result.score}/5 | Faithful: {result.faithful} | {result.reason}")

    avg_score = sum(r.score for r in results) / len(results)
    faithfulness_rate = sum(1 for r in results if r.faithful) / len(results)
    relevance_rate = sum(1 for r in results if r.relevant) / len(results)

    return EvalSummary(
        results=results,
        average_score=round(avg_score, 2),
        faithfulness_rate=round(faithfulness_rate * 100, 1),
        relevance_rate=round(relevance_rate * 100, 1),
    )


# Test cases: question + context your RAG retrieved + answer your RAG gave
TEST_CASES = [
    {
        "question": "What is the capital of France?",
        "context": "France is a country in Western Europe. Its capital city is Paris, which is also the largest city.",
        "answer": "The capital of France is Paris.",
    },
    {
        "question": "What is the population of France?",
        "context": "France is a country in Western Europe. Its capital city is Paris, which is also the largest city.",
        "answer": "France has a population of about 68 million people.",  # hallucination — not in context
    },
    {
        "question": "What is the capital of France?",
        "context": "France is a country in Western Europe. Its capital city is Paris, which is also the largest city.",
        "answer": "I don't know.",  # unhelpful
    },
]


if __name__ == "__main__":
    summary = run_eval(TEST_CASES)
    print(f"\n--- Eval Summary ---")
    print(f"Average score:     {summary.average_score}/5")
    print(f"Faithfulness rate: {summary.faithfulness_rate}%")
    print(f"Relevance rate:    {summary.relevance_rate}%")
