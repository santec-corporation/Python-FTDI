from src.ftd2xxhelper import Ftd2xxhelper


def test_initialize_without_serial():
    helper = Ftd2xxhelper()
    assert helper._ft_handle is not None
