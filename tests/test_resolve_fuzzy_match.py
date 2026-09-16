from bibcheck.resolve.base import Reference, Work
from bibcheck.resolve.fuzzy_match import compare


def test_match_requires_author_and_near_year():
    reference = Reference("raw", "A Paper", ["Jane Doe"], 2020)
    assert compare(reference, Work(title="A Paper", authors=["Jane Doe"], year=2020), .85).accepted
    assert not compare(reference, Work(title="A Paper", authors=["Jane Doe"], year=2023), .85).accepted
    assert not compare(reference, Work(title="A Paper", authors=["Other"], year=2020), .85).accepted


def test_match_normalizes_surname_with_full_indexed_author_name():
    reference = Reference("raw", "A Paper", ["Petrik, M.T."], 2020)
    work = Work(title="A Paper", authors=["Michael T. Petrik"], year=2020)

    assert compare(reference, work, .85).accepted
