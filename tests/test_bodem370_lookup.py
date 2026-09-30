from tools.build_bodem370_lookup import *
def test_known_corrections_are_guarded():
    assert KNOWN_CORRECTIONS[78]==(40,39)
    assert KNOWN_CORRECTIONS[95]==(28,31)
    assert KNOWN_CORRECTIONS[171]==(39,44)
    assert UNOBSERVED=={14,142,143,197,198}
