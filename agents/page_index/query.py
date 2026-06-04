import json
import sys
import pymupdf
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

TREE_PATH = "results/agreement_structure.json"
PDF_PATH = "/Users/abhishekkumar/Downloads/agreement.pdf"


def load_tree() -> dict:
    with open(TREE_PATH) as f:
        return json.load(f)


def get_page_text(pdf_path: str, start: int, end: int) -> str:
    doc = pymupdf.open(pdf_path)
    pages = []
    for i in range(start - 1, min(end, len(doc))):
        text = doc[i].get_text().strip()
        if text:
            pages.append(f"[Page {i+1}]\n{text}")
    return "\n\n".join(pages)


def find_relevant_sections(question: str, tree: dict) -> list[dict]:
    """Ask Claude to navigate the tree and pick relevant sections."""
    structure_summary = []
    for node in tree["structure"]:
        structure_summary.append({
            "node_id": node["node_id"],
            "title": node["title"],
            "pages": f"{node['start_index']}-{node['end_index']}",
            "summary": node.get("summary", ""),  # full summary — no truncation
        })

    prompt = f"""You are navigating a document tree index to find sections relevant to a question.

Question: {question}

Document structure (with summaries):
{json.dumps(structure_summary, indent=2)}

Select ALL node_ids whose content could help answer the question — including sections that partially relate.
Return ONLY a JSON array of node_ids. Example: ["0003", "0007", "0010"]"""

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    start = raw.find("[")
    end = raw.rfind("]") + 1
    node_ids = json.loads(raw[start:end])
    return [n for n in tree["structure"] if n["node_id"] in node_ids]


def build_context(sections: list[dict], pdf_path: str) -> str:
    context_parts = []
    for s in sections:
        header = f"=== {s['title']} (pages {s['start_index']}-{s['end_index']}) ==="
        text = get_page_text(pdf_path, s["start_index"], s["end_index"])
        if text.strip():
            # text-based PDF — use actual content
            context_parts.append(f"{header}\n{text}")
        else:
            # scanned PDF fallback — use tree summary
            context_parts.append(f"{header}\n[Summary]: {s.get('summary', '')}")
    return "\n\n".join(context_parts)


def answer_question(question: str, context: str) -> str:
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        system=(
            "You are a document analyst answering questions about a legal agreement. "
            "Use ONLY the provided document sections to answer. "
            "Be thorough and specific. Cite section titles and page numbers. "
            "If the answer spans multiple sections, cover all of them."
        ),
        messages=[{"role": "user", "content": f"Document sections:\n\n{context}\n\nQuestion: {question}"}],
    )
    return response.content[0].text


def query(question: str):
    print(f"\nQuestion: {question}")
    print("─" * 60)

    tree = load_tree()

    print("Step 1: Navigating tree to find relevant sections...")
    sections = find_relevant_sections(question, tree)
    if not sections:
        print("No relevant sections found.")
        return

    for s in sections:
        print(f"  → [{s['node_id']}] {s['title']} (pages {s['start_index']}-{s['end_index']})")

    print("Step 2: Loading page content...")
    context = build_context(sections, PDF_PATH)

    print("Step 3: Generating answer...\n")
    answer = answer_question(question, context)
    print(answer)


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What happens if I miss a payment?"
    query(q)
