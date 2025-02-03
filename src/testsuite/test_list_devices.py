from src.ftd2xxhelper import Ftd2xxhelper


def test_list_devices():
    devices = Ftd2xxhelper.list_devices()
    assert isinstance(devices, list)
    assert len(devices) >= 0
