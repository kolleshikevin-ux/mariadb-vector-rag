from search import semantic_search

TESTS = [
    {
        "question": "How does a CPU execute instructions?",
        "expected_categories": {"Computer Architecture"}
    },
    {
        "question": "What is mutual exclusion?",
        "expected_categories": {"Operating Systems"}
    },
    {
        "question": "What is a relational database?",
        "expected_categories": {"Databases"}
    },
    {
        "question": "Explain TCP/IP",
        "expected_categories": {"Networking"}
    },
    {
        "question": "What is a hash table?",
        "expected_categories": {"Algorithms"}
    },
    {
        "question": "How does virtual memory work?",
        "expected_categories": {"Operating Systems"}
    },
    {
        "question": "What are SQL joins?",
        "expected_categories": {"Databases"}
    },
    {
        "question": "Explain instruction pipelining",
        "expected_categories": {"Computer Architecture"}
    }
]

def evaluate():
    hits = 0
    for test in TESTS:
        rows = semantic_search(test["question"], limit=5)
        categories = [r[2] for r in rows]
        hit = any(c in test["expected_categories"] for c in categories)
        if hit:
            hits += 1

        print(test["question"])
        print("Top categories:", categories)
        print("Relevant result in top-5:", hit)
        print()

    print(f"Hit@5: {hits}/{len(TESTS)} = {hits/len(TESTS):.2%}")

if __name__ == "__main__":
    evaluate()
