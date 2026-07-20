from app.meetings.chunking import (
    CHUNK_SIZE_WORDS,
    OVERLAP_WORDS,
    SINGLE_PASS_WORD_THRESHOLD,
    split_into_chunks,
)


def _words(n: int) -> str:
    return " ".join(f"slowo{i}" for i in range(n))


def test_short_transcript_single_pass():
    text = _words(SINGLE_PASS_WORD_THRESHOLD - 1)
    assert split_into_chunks(text) == [text]


def test_empty_transcript_returns_single_empty_chunk():
    assert split_into_chunks("") == [""]


def test_long_transcript_splits_with_overlap():
    total_words = 9000
    text = _words(total_words)
    chunks = split_into_chunks(text)

    assert len(chunks) > 1
    # pierwszy fragment ma dokładnie CHUNK_SIZE_WORDS słów
    assert len(chunks[0].split()) == CHUNK_SIZE_WORDS

    # zakład: ostatnie OVERLAP_WORDS słów pierwszego fragmentu = pierwsze
    # OVERLAP_WORDS słów drugiego fragmentu.
    first_tail = chunks[0].split()[-OVERLAP_WORDS:]
    second_head = chunks[1].split()[:OVERLAP_WORDS]
    assert first_tail == second_head


def test_long_transcript_covers_all_words_without_gaps():
    total_words = 12000
    text = _words(total_words)
    words = text.split()
    chunks = split_into_chunks(text)

    # każde słowo oryginału pojawia się w co najmniej jednym fragmencie,
    # w tej samej kolejności (sklejone fragmenty pokrywają całość).
    covered = set()
    for chunk in chunks:
        covered.update(chunk.split())
    assert covered == set(words)

    # ostatni fragment kończy się na ostatnim słowie transkryptu
    assert chunks[-1].split()[-1] == words[-1]
