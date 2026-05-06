from backend.core.normalizer import TextNormalizer


def test_normalizes_case_dash_index_prefix_and_whitespace() -> None:
    normalizer = TextNormalizer()

    result = normalizer.normalize("  01. КИНО —   Группа   крови  ")

    assert result.normalized_text == "кино - группа крови"
    assert result.transformations == (
        "trimmed_outer_whitespace",
        "normalized_dash_characters",
        "removed_list_index_prefix",
        "lowercased_text",
        "collapsed_whitespace",
    )


def test_removes_special_characters_but_keeps_music_punctuation() -> None:
    normalizer = TextNormalizer()

    result = normalizer.normalize("AC/DC - It's a Long Way!!!")

    assert result.normalized_text == "ac/dc - it's a long way"
    assert "removed_special_characters" in result.transformations
