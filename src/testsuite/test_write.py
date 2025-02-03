from src.ftd2xxhelper import Ftd2xxhelper

devices = Ftd2xxhelper.list_devices()

wav = float(1515)
write_wav_command = f'WAV {wav}'
query_wav_command = 'WAV?'


def test_write():
    helper = Ftd2xxhelper(devices[0].SerialNumber)

    helper.write(command=write_wav_command)

    query_response = float(helper.query(query_wav_command))

    assert query_response == wav, f"Expected {wav}, but got {query_response}"
