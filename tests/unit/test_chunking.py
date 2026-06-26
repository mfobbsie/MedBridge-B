from app.services.chunking_service import chunk_document, needs_chunking, assemble_context, simple_keyword_retrieval, count_tokens

SHORT_TEXT = "The patient has high blood pressure. The doctor recommends lifestyle changes."
VERY_LONG_TEXT = "word " * 4100

def test_short_document_is_single_chunk():
    chunks = chunk_document(SHORT_TEXT)
    assert len(chunks) == 1

def test_long_document_produces_multiple_chunks():
    chunks = chunk_document(VERY_LONG_TEXT)
    assert len(chunks) > 1

def test_chunks_have_sequential_indices():
    chunks = chunk_document(VERY_LONG_TEXT)
    for i, chunk in enumerate(chunks):
        assert chunk.index == i

def test_chunk_token_counts_within_limit():
    from app.config import get_settings
    s = get_settings()
    for chunk in chunk_document(VERY_LONG_TEXT):
        assert chunk.token_count <= s.chunk_size_tokens + 10

def test_needs_chunking_short_doc():
    assert not needs_chunking(SHORT_TEXT)

def test_needs_chunking_long_doc():
    assert needs_chunking(VERY_LONG_TEXT)

def test_assemble_context_respects_limit():
    result = assemble_context(["word " * 100] * 4, max_tokens=200)
    assert count_tokens(result) <= 220

def test_assemble_context_all_chunks_fit():
    result = assemble_context(["hello world", "foo bar"], max_tokens=1000)
    assert "hello world" in result and "foo bar" in result

def test_keyword_retrieval_ranks_by_overlap():
    chunks = ["high blood pressure hypertension", "weather is nice", "blood pressure medication"]
    results = simple_keyword_retrieval(chunks, "blood pressure medication", top_k=2)
    assert "weather" not in results[0] and len(results) == 2

def test_keyword_retrieval_fallback_on_empty_question():
    results = simple_keyword_retrieval(["a", "b", "c"], "what is the", top_k=2)
    assert len(results) == 2