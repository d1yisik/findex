from __future__ import annotations

import math
from findex.builder import Index, open_index
from findex.models import DocMeta, Posting
from findex.query_ast import And, Not, Or, Phrase, Term, parse_query
from findex.ranking import BM25, TfIdf, rank_documents


def test_ast_parser():
    print("=== 1. AST Parser Unit Tests ===")
    q1 = 'python AND (async OR await) NOT java "event loop"'
    parsed1 = parse_query(q1)
    
    expected1 = And(
        And(
            And(
                Term("python"),
                Or(Term("async"), Term("await"))
            ),
            Not(Term("java"))
        ),
        Phrase("event loop")
    )
    assert parsed1 == expected1, f"AST mismatch:\nActual: {parsed1!r}\nExpected: {expected1!r}"
    print("AST Parser: дерево виразу з дужками, фразами та операторами розпарсено вірно!\n")


def test_ranking_sanity_checks(index: Index):
    print("=== 2. Три Sanity-Check рейтингу (BM25) ===")
    bm25 = BM25(index)

    # Sanity check 1: Рідкісний термін має вищий IDF і score, ніж частий
    score_rare = bm25.score_term("перший", tf=1, doc_len=5)
    score_frequent = bm25.score_term("документ", tf=1, doc_len=5)
    print(f"1. Рідкісний ('перший'): {score_rare:.4f} > Частий ('документ'): {score_frequent:.4f}")
    assert score_rare > score_frequent, "Sanity Check 1 Failed!"

    # Sanity check 2: 20-те повторення додає набагато менше за 1-ше (насичення TF)
    s1 = bm25.score_term("тестовий", tf=1, doc_len=30)
    s19 = bm25.score_term("тестовий", tf=19, doc_len=30)
    s20 = bm25.score_term("тестовий", tf=20, doc_len=30)
    gain_first = s1
    gain_20th = s20 - s19
    print(f"2. Приріст від 1-го входження: {gain_first:.4f} vs 20-го: {gain_20th:.4f} (приріст згасає)")
    assert gain_first > gain_20th * 5, "Sanity Check 2 Failed!"

    # Sanity check 3: Короткий документ з tf=1 ранжується вище за довгий з tf=1
    score_short = bm25.score_term("тестовий", tf=1, doc_len=5)
    score_long = bm25.score_term("тестовий", tf=1, doc_len=50)
    print(f"3. Короткий документ (len=5): {score_short:.4f} > Довгий (len=50): {score_long:.4f}")
    assert score_short > score_long, "Sanity Check 3 Failed!"
    print("Усі 3 sanity-перевірки успішно пройдені!\n")


def evaluate_precision_at_5(index: Index):
    print("=== 3. Оцінка Precision@5 (TF-IDF vs BM25) на 10 запитах ===")
    
    test_suite = [
        ("перший", {"doc1.txt"}),
        ("другий", {"doc2.txt"}),
        ("третій", {"doc3.txt"}),
        ("документ", {"doc1.txt", "doc2.txt", "doc3.txt"}),
        ("тестовий", {"doc1.txt", "doc2.txt", "doc3.txt"}),
        ("перший документ", {"doc1.txt"}),
        ("другий документ", {"doc2.txt"}),
        ("третій документ", {"doc3.txt"}),
        ('"перший тестовий"', {"doc1.txt"}),
        ("документ NOT перший", {"doc2.txt", "doc3.txt"}),
    ]

    tfidf_precisions = []
    bm25_precisions = []

    print(f"{'№':<3} | {'Запит':<25} | {'TF-IDF P@5':<12} | {'BM25 P@5':<12}")
    print("-" * 60)

    for i, (q, rel_docs) in enumerate(test_suite, start=1):
        ast = parse_query(q)
        matched = ast.evaluate(index)

        # Оцінка TF-IDF
        terms = [t.lower() for t in q.replace('"', '').split() if t not in ('NOT', 'AND', 'OR')]
        res_tfidf = rank_documents(index, terms, matched, TfIdf(index), top_k=5)
        found_tfidf = {r.path for r in res_tfidf}
        p5_tfidf = len(found_tfidf & rel_docs) / min(5, max(1, len(rel_docs)))
        tfidf_precisions.append(p5_tfidf)

        # Оцінка BM25
        res_bm25 = rank_documents(index, terms, matched, BM25(index), top_k=5)
        found_bm25 = {r.path for r in res_bm25}
        p5_bm25 = len(found_bm25 & rel_docs) / min(5, max(1, len(rel_docs)))
        bm25_precisions.append(p5_bm25)

        print(f"{i:<3} | {q:<25} | {p5_tfidf:<12.2f} | {p5_bm25:<12.2f}")

    mean_tfidf = sum(tfidf_precisions) / len(tfidf_precisions)
    mean_bm25 = sum(bm25_precisions) / len(bm25_precisions)
    print("-" * 60)
    print(f"Mean Average P@5: TF-IDF = {mean_tfidf:.2f}, BM25 = {mean_bm25:.2f}\n")

if __name__ == "__main__":
    test_ast_parser()
    with open_index("index.bin") as idx:
        test_ranking_sanity_checks(idx)
        evaluate_precision_at_5(idx)