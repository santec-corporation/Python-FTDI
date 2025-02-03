from src.ftd2xxhelper import Ftd2xxhelper

devices = Ftd2xxhelper.list_devices()


def test_query_idn():
    helper = Ftd2xxhelper(devices[0].SerialNumber)
    response = helper.query_idn()
    assert isinstance(response, str)
    assert len(response) > 0
