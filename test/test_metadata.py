from earthlib.metadata import Schema


def test_Schema():
    s = Schema(
        NAME="TestSample",
        LEVEL_1="pervious",
        LEVEL_2="vegetation",
        LEVEL_3="measured",
        LEVEL_4="any_label",
    )
    assert s.NAME == "TestSample"
    assert s.LEVEL_1 == "pervious"
    assert s.LEVEL_2 == "vegetation"
    assert s.LEVEL_3 == "measured"
    assert s.LEVEL_4 == "any_label"
    assert s.LAT is None
    assert s.LON is None
    assert s.SOURCE is None
    assert s.NOTES is None

    s_copy = s.copy()
    assert s_copy == s
    assert s_copy is not s
