from app.resolver import PersonRecord, resolve_name

JAN = PersonRecord(id="jan", full_name="Jan Kowalski", aliases=["Janek", "Jan K."])
ANNA_N = PersonRecord(id="anna-n", full_name="Anna Nowak", aliases=["Ania"])
ANNA_W = PersonRecord(id="anna-w", full_name="Anna Wiśniewska", aliases=[])
PIOTR = PersonRecord(id="piotr", full_name="Piotr Zieliński", aliases=["Piotrek"])

PEOPLE = [JAN, ANNA_N, ANNA_W, PIOTR]


def test_exact_full_name_match_case_insensitive():
    assert resolve_name("jan kowalski", PEOPLE) == "jan"
    assert resolve_name("Jan Kowalski", PEOPLE) == "jan"


def test_alias_match():
    assert resolve_name("Janek", PEOPLE) == "jan"
    assert resolve_name("Ania", PEOPLE) == "anna-n"


def test_unique_first_name_match():
    assert resolve_name("Piotr", PEOPLE) == "piotr"


def test_ambiguous_first_name_returns_none_not_random_pick():
    """Kluczowy wymóg z ETAPY.md: dwie osoby o imieniu Anna -> None, nie zgadywanie."""
    assert resolve_name("Anna", PEOPLE) is None


def test_ambiguous_alias_collision_returns_none():
    people = [
        PersonRecord(id="a", full_name="Aleksandra Kowal", aliases=["Ola"]),
        PersonRecord(id="b", full_name="Ola Bąk", aliases=["Ola"]),
    ]
    assert resolve_name("Ola", people) is None


def test_fuzzy_trigram_match_above_threshold():
    people = [PersonRecord(id="x", full_name="Krzysztof Zawadzki", aliases=[])]
    # literówka / odmiana, ale wystarczająco bliska
    assert resolve_name("Krzystof Zawadzki", people) == "x"


def test_fuzzy_trigram_ambiguous_returns_none():
    people = [
        PersonRecord(id="a", full_name="Marta Wilk", aliases=[]),
        PersonRecord(id="b", full_name="Marta Wolk", aliases=[]),
    ]
    assert resolve_name("Marta Wlk", people) is None


def test_no_match_returns_none():
    assert resolve_name("Zbigniew Religa", PEOPLE) is None


def test_empty_or_blank_input_returns_none():
    assert resolve_name("", PEOPLE) is None
    assert resolve_name("   ", PEOPLE) is None


def test_full_name_exact_match_takes_priority_over_alias_collision():
    people = [
        PersonRecord(id="a", full_name="Jan Nowak", aliases=[]),
        PersonRecord(id="b", full_name="Jan Kowalski", aliases=["Jan Nowak"]),
    ]
    # "Jan Nowak" pasuje dokładnie do full_name osoby "a" -> krok 1 rozstrzyga
    # zanim dojdzie do (kolidującego) aliasu osoby "b".
    assert resolve_name("Jan Nowak", people) == "a"
