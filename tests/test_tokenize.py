from catalog_rag.retrievers.bm25 import tokenize as bm25_tokenize
from catalog_rag.retrievers.tokenize import tokenize


def test_fused_token_present_alongside_plain_tokens():
    toks = tokenize("what do I need before ECEN 350?", fuse_codes=True)
    assert "ecen350" in toks
    assert "ecen" in toks and "350" in toks


def test_spacing_and_case_variants_collapse_to_one_token():
    variants = ["ECEN 350", "ECEN350", "ecen 350", "Ecen350"]
    outs = {tuple(tokenize(v, fuse_codes=True)) for v in variants}
    assert outs == {("ecen", "350", "ecen350")}


def test_plain_text_unchanged_and_default_matches_bm25():
    plain = "linear time-invariant systems; Fourier analysis"
    assert tokenize(plain, fuse_codes=True) == tokenize(plain)
    for s in [plain, "ECEN 350 and CSCE 120; junior classification"]:
        assert tokenize(s) == bm25_tokenize(s)
    assert tokenize("ECEN 350") == ["ecen", "350"]


def test_suffix_letter_and_no_midword_fusion():
    assert "math151h" in tokenize("MATH 151H", fuse_codes=True)
    assert tokenize("abcd1234", fuse_codes=True) == ["abcd1234"]
