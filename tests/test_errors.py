from http import HTTPStatus

from tools.youtube_mcp import errors


def test_error_subclasses_expose_codes():
    exc = errors.VideoUnavailable()
    assert exc.to_dict()["code"] == "VideoUnavailable"
    assert exc.http_status == HTTPStatus.NOT_FOUND

    network = errors.NetworkError("oops")
    assert network.to_dict()["message"] == "oops"
    assert network.http_status == HTTPStatus.SERVICE_UNAVAILABLE
