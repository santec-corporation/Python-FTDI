from src.ftd2xxhelper import Ftd2xxhelper

serial_number = 23110067
serial_number_to_byte = str(serial_number).encode('utf-8')


def test_initialize_with_serial():
    helper = Ftd2xxhelper(serial_number_to_byte)
    assert helper._ft_handle is not None
    assert helper._last_connected_serial_number.decode('ascii') == str(serial_number)
