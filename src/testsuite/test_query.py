from src.ftd2xxhelper import Ftd2xxhelper

devices = Ftd2xxhelper.list_devices()

command = 'POW?'


def test_query_idn():
    helper = Ftd2xxhelper(devices[0].SerialNumber)
    response = helper.query(command=command)
    assert isinstance(response, str)
    assert len(response) > 0
