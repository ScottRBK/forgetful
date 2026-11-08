"""Integration tests for keyword query builder."""

from app.utils.keyword_query import build_keyword_query, to_fts5_match, to_pg_tsquery


def test_ticket_key():
    kq = build_keyword_query("PAY-6538")
    assert list(kq.terms) == ["pay", "6538"]
    assert list(kq.phrases) == [("pay", "6538")]
    assert to_fts5_match(kq) == '"pay" OR "6538" OR "pay 6538"'
    assert to_pg_tsquery(kq) == "pay | 6538 | pay <-> 6538"


def test_snake_case_symbol():
    kq = build_keyword_query("`truncate_memories_by_budget`")
    assert list(kq.terms) == [
        "truncate",
        "memories",
        "by",
        "budget",
    ]
    assert list(kq.phrases) == [("truncate", "memories", "by", "budget")]
    assert len(kq.terms) == 4


def test_hash_number():
    kq = build_keyword_query("#2753")
    assert list(kq.terms) == ["2753"]
    assert kq.phrases == ()


def test_special_operators_stripped():
    kq = build_keyword_query('say "hi" NEAR(x) a* -b :c')
    match = to_fts5_match(kq)
    assert "*" not in match
    assert "(" not in match
    assert ":" not in match
    assert "NEAR" not in match
    assert " -" not in match and not match.startswith("-")


def test_empty_queries():
    assert build_keyword_query("").is_empty
    assert build_keyword_query("!!! ...").is_empty


def test_max_terms_cap():
    words = " ".join(f"w{i:02d}" for i in range(40))
    kq = build_keyword_query(words)
    assert len(kq.terms) == 32


def test_short_runs_dropped():
    kq = build_keyword_query("a b")
    assert kq.is_empty


def test_unicode_letter_is_one_term():
    kq = build_keyword_query("résumé")
    assert list(kq.terms) == ["résumé"]
    assert kq.phrases == ()


def test_dotted_name_and_path_split_on_punctuation():
    dotted = build_keyword_query("ledger.db.session")
    assert list(dotted.terms) == ["ledger", "db", "session"]
    assert list(dotted.phrases) == [("ledger", "db", "session")]

    path = build_keyword_query("src/app/main.py")
    assert list(path.terms) == ["src", "app", "main", "py"]
    assert ("src", "app", "main", "py") in path.phrases
