from app.meetings.review import _compute_decision_unresolved, _compute_task_unresolved


def test_no_raci_mentioned_is_not_unresolved():
    # AI nie wskazało ani R, ani A, ani C/I — to poprawny stan (§10.2: "nie
    # zgaduj"), nie powinien blokować zatwierdzenia.
    assert _compute_task_unresolved({}, None, None, 0, 0) is False


def test_r_mentioned_but_not_resolved_blocks():
    raci_raw = {"R": "Janek", "A": None, "C": [], "I": []}
    assert _compute_task_unresolved(raci_raw, None, None, 0, 0) is True


def test_r_mentioned_and_resolved_does_not_block():
    raci_raw = {"R": "Janek", "A": None, "C": [], "I": []}
    assert _compute_task_unresolved(raci_raw, "person-1", None, 0, 0) is False


def test_a_mentioned_but_not_resolved_blocks_even_if_r_ok():
    raci_raw = {"R": "Janek", "A": "Ktoś Nieznany", "C": [], "I": []}
    assert _compute_task_unresolved(raci_raw, "person-1", None, 0, 0) is True


def test_c_partially_resolved_blocks():
    raci_raw = {"R": None, "A": None, "C": ["Piotr", "Ania"], "I": []}
    # tylko jedna z dwóch osób C została rozwiązana -> nadal blokuje
    assert _compute_task_unresolved(raci_raw, None, None, 1, 0) is True


def test_c_fully_resolved_does_not_block():
    raci_raw = {"R": None, "A": None, "C": ["Piotr", "Ania"], "I": []}
    assert _compute_task_unresolved(raci_raw, None, None, 2, 0) is False


def test_i_partially_resolved_blocks():
    raci_raw = {"R": None, "A": None, "C": [], "I": ["Zarząd"]}
    assert _compute_task_unresolved(raci_raw, None, None, 0, 0) is True


def test_decision_no_decided_by_mentioned_not_unresolved():
    assert _compute_decision_unresolved(None, None) is False


def test_decision_decided_by_mentioned_but_unresolved_blocks():
    assert _compute_decision_unresolved("Ktoś Nieznany", None) is True


def test_decision_decided_by_resolved_does_not_block():
    assert _compute_decision_unresolved("Jan Kowalski", "person-1") is False
