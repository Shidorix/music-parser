from backend.core.services import ParseService


def test_parse_service_returns_parser_only_result() -> None:
    service = ParseService()

    result = service.parse_lines(["Daft Punk - Around the World", ""])

    assert result.total == 1
    assert result.items[0].artist == "daft punk"
    assert result.items[0].title == "around the world"
    assert result.items[0].language.value == "en"


def test_parse_service_can_keep_blank_lines() -> None:
    service = ParseService()

    result = service.parse_lines([""], skip_blank=False)

    assert result.total == 1
    assert result.items[0].normalized_input == ""
