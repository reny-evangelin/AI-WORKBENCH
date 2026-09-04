import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag.retriever import retrieve


def test_retrieve():
    query = "What safety precautions are required before maintenance?"
    results = retrieve(query, n_results=2)

    print(f"Query: {query}\n")
    for i, match in enumerate(results, start=1):
        print(f"Result {i} (distance={match['distance']:.4f})")
        print("Text:", match["text"][:150], "...")
        print("Metadata:", match["metadata"])
        print()


if __name__ == "__main__":
    test_retrieve()