# -*- coding: utf-8 -*-
# !/usr/bin/env python

import sys
import time
import ctypes
import struct
import string
from ctypes import Array
from typing import List, Any


class FtNode(ctypes.Structure):
    _fields_ = [
        ("Flags", ctypes.c_uint32),
        ("Type", ctypes.c_uint32),
        ("ID", ctypes.c_uint32),
        ("LocId", ctypes.c_uint32),
        ("SerialNumber", ctypes.c_char * 16),
        ("Description", ctypes.c_char * 64),
        ("FTHandle", ctypes.c_void_p),
    ]


class FtProgramData(ctypes.Structure):
    _fields_ = [
        ("Signature1", ctypes.c_uint32),
        ("Signature2", ctypes.c_uint32),
        ("Version", ctypes.c_uint32),
        ("VendorId", ctypes.c_uint16),
        ("ProductId", ctypes.c_uint16),
        ("Manufacturer", ctypes.POINTER(ctypes.c_char)),
        ("ManufacturerId", ctypes.POINTER(ctypes.c_char)),
        ("Description", ctypes.POINTER(ctypes.c_char)),
        ("SerialNumber", ctypes.POINTER(ctypes.c_char)),
        ("MaxPower", ctypes.c_uint16),
        ("PnP", ctypes.c_uint16),
        ("SelfPowered", ctypes.c_uint16),
        ("RemoteWakeup", ctypes.c_uint16),
    ]


class Ftd2xxhelper(object):
    terminator = "\r"

    def __init__(self, serialNumber: str | bytes | None = None):
        self.__SelectedDeviceNode = None
        self.lastConnectedSerialNumber = None
        self.ftHandle = None
        self.numDevices = None
        self.ftdiDeviceList = None

        if sys.platform.startswith("linux"):
            self.d2xx = ctypes.cdll.LoadLibrary("libft2xx.so")
        elif sys.platform.startswith("darwin"):
            self.d2xx = ctypes.cdll.LoadLibrary("libftd2xx.dylib")
        else:
            self.d2xx = ctypes.windll.LoadLibrary("ftd2xx")

        self.initialize(serialNumber)

    @staticmethod
    def __check(f):
        if f != 0:
            names = [
                "FT_OK",
                "FT_INVALID_HANDLE",
                "FT_DEVICE_NOT_FOUND",
                "FT_DEVICE_NOT_OPENED",
                "FT_IO_ERROR",
                "FT_INSUFFICIENT_RESOURCES",
                "FT_INVALID_PARAMETER",
                "FT_INVALID_BAUD_RATE",
                "FT_DEVICE_NOT_OPENED_FOR_ERASE",
                "FT_DEVICE_NOT_OPENED_FOR_WRITE",
                "FT_FAILED_TO_WRITE_DEVICE",
                "FT_EEPROM_READ_FAILED",
                "FT_EEPROM_WRITE_FAILED",
                "FT_EEPROM_ERASE_FAILED",
                "FT_EEPROM_NOT_PRESENT",
                "FT_EEPROM_NOT_PROGRAMMED",
                "FT_INVALID_ARGS",
                "FT_NOT_SUPPORTED",
                "FT_OTHER_ERROR",
            ]
            raise IOError("Error: (status %d: %s)" % (f, names[f]))

    @staticmethod
    def list_devices():
        d2xx = None
        if sys.platform.startswith("linux"):
            d2xx = ctypes.cdll.LoadLibrary("libft2xx.so")
        elif sys.platform.startswith("darwin"):
            d2xx = ctypes.cdll.LoadLibrary("libftd2xx.dylib")
        else:
            d2xx = ctypes.windll.LoadLibrary("ftd2xx")
        if d2xx is None:
            return []
        numDevs = ctypes.c_long()
        Ftd2xxhelper.__check(d2xx.FT_CreateDeviceInfoList(ctypes.byref(numDevs)))
        ftdiDeviceList = []
        if numDevs.value > 0:
            t_devices = FtNode * numDevs.value
            devices = t_devices()
            Ftd2xxhelper.__check(
                d2xx.FT_GetDeviceInfoList(devices, ctypes.byref(numDevs))
            )
            for device in devices:
                ftHandle = ctypes.c_void_p()
                Ftd2xxhelper.__check(
                    d2xx.FT_OpenEx(device.SerialNumber, 1, ctypes.byref(ftHandle))
                )
                eeprom = FtProgramData()
                eeprom.Signature1 = 0x00000000
                eeprom.Signature2 = 0xFFFFFFFF
                eeprom.Version = 2
                eeprom.Manufacturer = ctypes.create_string_buffer(32)
                eeprom.ManufacturerId = ctypes.create_string_buffer(16)
                eeprom.Description = ctypes.create_string_buffer(64)
                eeprom.SerialNumber = ctypes.create_string_buffer(16)
                try:
                    Ftd2xxhelper.__check(
                        d2xx.FT_EE_Read(ftHandle, ctypes.byref(eeprom))
                    )
                    manufacturer = ctypes.cast(eeprom.Manufacturer, ctypes.c_char_p)
                    if manufacturer.value.decode("ascii").upper() == "SANTEC":
                        ftdiDeviceList.append(device)
                finally:
                    d2xx.FT_Close(ftHandle)
            return ftdiDeviceList
        else:
            return []

    def get_dev_info_list(self) -> Array[FtNode] | list[Any]:
        numDevs = ctypes.c_long()
        Ftd2xxhelper.__check(self.d2xx.FT_CreateDeviceInfoList(ctypes.byref(numDevs)))
        self.numDevices = numDevs.value
        if numDevs.value > 0:
            t_devices = FtNode * numDevs.value
            devices = t_devices()
            Ftd2xxhelper.__check(
                self.d2xx.FT_GetDeviceInfoList(devices, ctypes.byref(numDevs))
            )
            self.ftdiDeviceList = devices
            return devices
        else:
            return []

    def eeprom_data(self):
        if self.__SelectedDeviceNode is None:
            return None

        eeprom = FtProgramData()
        eeprom.Signature1 = 0x00000000
        eeprom.Signature2 = 0xFFFFFFFF
        eeprom.Version = 2
        eeprom.Manufacturer = ctypes.create_string_buffer(32)
        eeprom.ManufacturerId = ctypes.create_string_buffer(16)
        eeprom.Description = ctypes.create_string_buffer(64)
        eeprom.SerialNumber = ctypes.create_string_buffer(16)

        try:
            Ftd2xxhelper.__check(
                self.d2xx.FT_EE_Read(self.ftHandle, ctypes.byref(eeprom))
            )
            return eeprom
        except:
            return None

    def initialize(self, serialNumber: str | bytes | None = None):
        devs = self.get_dev_info_list()

        self.__SelectedDeviceNode = None
        self.lastConnectedSerialNumber = None

        if serialNumber is None:
            for dev in devs:
                if dev.Description.decode("ascii").startswith("TSL"):
                    self.__SelectedDeviceNode = dev
                    self.lastConnectedSerialNumber = dev.SerialNumber
                    break
        else:
            for dev in devs:
                if (
                        dev.SerialNumber == serialNumber
                        or dev.SerialNumber.decode("ascii") == serialNumber
                ):
                    self.__SelectedDeviceNode = dev
                    self.lastConnectedSerialNumber = dev.SerialNumber
                    break
        if self.__SelectedDeviceNode is None:
            if serialNumber is None:
                raise ValueError("Failed to find Santec instruments")
            raise ValueError(f"Failed to open device by serial number '{serialNumber}'")
        self.ftHandle = ctypes.c_void_p()
        Ftd2xxhelper.__check(
            self.d2xx.FT_OpenEx(
                self.lastConnectedSerialNumber, 1, ctypes.byref(self.ftHandle)
            )
        )

        eeprom = self.eeprom_data()
        if eeprom is None:
            raise RuntimeError(
                f"Failed to retrieve EEPROM data from the device (SN: {self.lastConnectedSerialNumber}, Description: {self.__SelectedDeviceNode.Description})"
            )
        manufacturer = ctypes.cast(eeprom.Manufacturer, ctypes.c_char_p)
        if manufacturer.value.decode("ascii").upper() == "SANTEC":
            self.__initialize()

    def __initialize(self):
        word_len = ctypes.c_ubyte(8)
        stop_bits = ctypes.c_ubyte(0)
        parity = ctypes.c_ubyte(0)
        Ftd2xxhelper.__check(
            self.d2xx.FT_SetDataCharacteristics(
                self.ftHandle, word_len, stop_bits, parity
            )
        )
        flowControl = ctypes.c_uint16(0x00)
        xon = ctypes.c_ubyte(17)
        x_off = ctypes.c_ubyte(19)
        Ftd2xxhelper.__check(
            self.d2xx.FT_SetFlowControl(self.ftHandle, flowControl, xon, x_off)
        )
        baud_rate = ctypes.c_uint64(9600)
        Ftd2xxhelper.__check(self.d2xx.FT_SetBaudRate(self.ftHandle, baud_rate))
        timeout = ctypes.c_uint64(1000)
        Ftd2xxhelper.__check(self.d2xx.FT_SetTimeouts(self.ftHandle, timeout, timeout))
        mask = ctypes.c_ubyte(0x00)
        enable = ctypes.c_ubyte(0x40)
        Ftd2xxhelper.__check(self.d2xx.FT_SetBitMode(self.ftHandle, mask, enable))

    def open_usb_connection(self):
        self.initialize()

    def close_usb_connection(self):
        if self.ftHandle is not None:
            self.d2xx.FT_Close(self.ftHandle)
            self.ftHandle = None

    def disconnect(self):
        self.close_usb_connection()

    def write(self, command: str):
        try:
            idx = command.index(self.terminator)
            if idx == 0:
                raise ValueError(
                    "The first character of the write command cannot be the command terminator"
                )
            elif not command.endswith(self.terminator):
                command = command[:idx]
        except ValueError:
            command = command + self.terminator

        if self.ftHandle is None:
            self.ftHandle = ctypes.c_void_p()
            Ftd2xxhelper.__check(
                self.d2xx.FT_OpenEx(
                    self.lastConnectedSerialNumber, 1, ctypes.byref(self.ftHandle)
                )
            )

        written = ctypes.c_uint()
        commandLen = len(command)
        cmd = (ctypes.c_ubyte * commandLen).from_buffer_copy(command.encode("ascii"))
        Ftd2xxhelper.__check(
            self.d2xx.FT_Write(self.ftHandle, cmd, commandLen, ctypes.byref(written))
        )
        time.sleep(0.020)

    def read(self, maxTimeToWait: float = 0.020, totalNumberOfBytesToRead: int = 0):
        if self.ftHandle is None:
            self.ftHandle = ctypes.c_void_p()
            Ftd2xxhelper.__check(
                self.d2xx.FT_OpenEx(
                    self.lastConnectedSerialNumber, 1, ctypes.byref(self.ftHandle)
                )
            )

        timeCounter = 0.0
        sleepTimer = 0.020

        binaryData = bytearray()
        read = False

        while timeCounter < maxTimeToWait:
            bytesRead = ctypes.c_uint()
            available = ctypes.c_uint()
            timeCounter += sleepTimer
            time.sleep(sleepTimer)
            Ftd2xxhelper.__check(
                self.d2xx.FT_GetQueueStatus(self.ftHandle, ctypes.byref(available))
            )
            if available.value > 0:
                read = True
            elif available.value == 0:
                if read:
                    break
                else:
                    continue
            arr = (ctypes.c_ubyte * available.value)()
            Ftd2xxhelper.__check(
                self.d2xx.FT_Read(
                    self.ftHandle, arr, available, ctypes.byref(bytesRead)
                )
            )
            buf = bytearray(arr)
            binaryData.extend(buf)

            if bytesRead.value > 0:
                timeCounter = 0

            if (
                    0 < totalNumberOfBytesToRead <= len(binaryData)
            ):
                break

        self.close_usb_connection()
        return binaryData

    def query_idn(self):
        return self.query("*IDN?")

    def query(self, command: str, waitTime: int = 1):
        if self.ftHandle is None:
            self.ftHandle = ctypes.c_void_p()
            Ftd2xxhelper.__check(
                self.d2xx.FT_OpenEx(
                    self.lastConnectedSerialNumber, 1, ctypes.byref(self.ftHandle)
                )
            )

        self.write(command)

        arr = self.read(waitTime)

        response_str = ""
        try:
            response_str = arr.decode("ascii")
        except UnicodeDecodeError:
            print(arr)
            return response_str

        if len(response_str) < 3:
            return response_str.strip()
        elif response_str[0] == "\0":
            return response_str

        trimmed = self.__remove_prefix_from_result_if_not_hex(response_str.strip())

        try:
            idx = trimmed.rindex(self.terminator)
            if len(trimmed) - 2 > idx:
                trimmed = trimmed[(idx + 1):].strip()
        except ValueError:
            pass

        if trimmed == response_str.strip():
            return trimmed

        return response_str

    @staticmethod
    def __remove_prefix_from_result_if_not_hex(result_str: str):
        if result_str is None or len(result_str) < 3:
            return result_str

        if result_str[0] == "\0":
            return result_str

        # if result_str[0] not in result_str.hexdigits or result_str[1] not in result_str.hexdigits:
        #     return result_str[2:]

        if result_str[0] not in string.hexdigits or result_str[1] not in string.hexdigits:
            return result_str[2:]

        return result_str

    def get_all_dat_points_from_last_scan_scpi_command(self):
        getCountCommand = "READout:POINts?"
        getDataCommand = "READout:DATa?"

        points = 0
        response_str = self.query(getCountCommand)
        print(response_str)
        try:
            points = int(response_str)
        except ValueError:
            raise RuntimeError(
                f"Failed to retrieve a valid number of data points from the last scan: {response_str}"
            )

        if points > 200001:
            raise ValueError(
                f"The number of data points received from the last scan is too large: {points}"
            )

        self.write(getDataCommand)
        time.sleep(5)
        arr = self.read(1, points * 4)
        if len(arr) == 0:
            return arr

        if arr[0] != ord("#"):
            print(arr[0])
            raise ValueError(
                f"The value read was supposed to contain a # symbol as the first byte, but contained '{arr[0]}'"
            )

        b = chr(arr[1])
        try:
            val = int(b)
        except Exception as e:
            print(arr[1], b)
            raise ValueError(
                f"The value read was supposed to contain a number as the second byte, but contained '{b}', {e}"
            )

        b = "".join(map(chr, arr[2: 2 + val]))
        try:
            num = int(b)
        except Exception as e:
            print(arr[2: 2 + val], b)
            raise ValueError(
                f"The value read was supposed to contain a number, but contained '{b}', {e}"
            )

        offset = 2 + val
        return list(
            map(
                lambda x: struct.unpack(">f", x),
                Ftd2xxhelper.__chunks(arr[offset:], num, 4),
            )
        )

    def get_all_data_points_from_last_scan_santec_command(self):
        getCountCommand = "TN"
        getDataCommand = "TA"

        points = int(self.query(getCountCommand))

        self.write(getDataCommand)
        arr = self.read(1, points * 4)

        if len(arr) != points * 4:
            raise ValueError(
                f"Invalid data with mismatch length returned, expect: {points}, got: {len(arr)}"
            )

        if sys.version_info[1] >= 12:
            import itertools

            return list(
                map(lambda x: int.from_bytes(x, "big"), itertools.batched(arr, 4))
            )

        return list(
            map(
                lambda x: int.from_bytes(x, "big"),
                Ftd2xxhelper.__chunks(arr, points, 4),
            )
        )

    @staticmethod
    def __chunks(arr: bytearray, length: int, n: int = 4):
        for i in range(0, length):
            yield arr[i * n: i * n + n]
