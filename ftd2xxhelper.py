# -*- coding: utf-8 -*-
# !/usr/bin/env python

"""
Santec Python FTDI
Script to control Santec instruments via USB.

@organization: santec holdings corp.
"""

import sys
import time
import ctypes
import struct
import string


class FT_Node(ctypes.Structure):
    _fields_ = [
        ("Flags", ctypes.c_uint32),
        ("Type", ctypes.c_uint32),
        ("ID", ctypes.c_uint32),
        ("LocId", ctypes.c_uint32),
        ("SerialNumber", ctypes.c_char * 16),
        ("Description", ctypes.c_char * 64),
        ("FTHandle", ctypes.c_void_p),
    ]


class FT_Program_Data(ctypes.Structure):
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


class FTD2XXHelper(object):
    terminator = "\r"

    def __init__(self, serialNumber: str | bytes | None = None):
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
    def ListDevices():
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
        FTD2XXHelper.__check(d2xx.FT_CreateDeviceInfoList(ctypes.byref(numDevs)))
        ftdiDeviceList = []
        if numDevs.value > 0:
            t_devices = FT_Node * numDevs.value
            devices = t_devices()
            FTD2XXHelper.__check(
                d2xx.FT_GetDeviceInfoList(devices, ctypes.byref(numDevs))
            )
            for device in devices:
                ftHandle = ctypes.c_void_p()
                FTD2XXHelper.__check(
                    d2xx.FT_OpenEx(device.SerialNumber, 1, ctypes.byref(ftHandle))
                )
                eeprom = FT_Program_Data()
                eeprom.Signature1 = 0x00000000
                eeprom.Signature2 = 0xFFFFFFFF
                eeprom.Version = 2
                eeprom.Manufacturer = ctypes.create_string_buffer(32)
                eeprom.ManufacturerId = ctypes.create_string_buffer(16)
                eeprom.Description = ctypes.create_string_buffer(64)
                eeprom.SerialNumber = ctypes.create_string_buffer(16)
                try:
                    FTD2XXHelper.__check(
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

    def getDevInfoList(self) -> ctypes.Array[FT_Node]:
        numDevs = ctypes.c_long()
        FTD2XXHelper.__check(self.d2xx.FT_CreateDeviceInfoList(ctypes.byref(numDevs)))
        self.numDevices = numDevs.value
        if numDevs.value > 0:
            t_devices = FT_Node * numDevs.value
            devices = t_devices()
            FTD2XXHelper.__check(
                self.d2xx.FT_GetDeviceInfoList(devices, ctypes.byref(numDevs))
            )
            self.ftdiDeviceList = devices
            return devices
        else:
            return []

    def EEPROMData(self):
        if self.__SelectedDeviceNode is None:
            return None

        eeprom = FT_Program_Data()
        eeprom.Signature1 = 0x00000000
        eeprom.Signature2 = 0xFFFFFFFF
        eeprom.Version = 2
        eeprom.Manufacturer = ctypes.create_string_buffer(32)
        eeprom.ManufacturerId = ctypes.create_string_buffer(16)
        eeprom.Description = ctypes.create_string_buffer(64)
        eeprom.SerialNumber = ctypes.create_string_buffer(16)

        try:
            FTD2XXHelper.__check(
                self.d2xx.FT_EE_Read(self.ftHandle, ctypes.byref(eeprom))
            )
            return eeprom
        except:
            return None

    def initialize(self, serialNumber: str | bytes | None = None):
        devs = self.getDevInfoList()

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
        FTD2XXHelper.__check(
            self.d2xx.FT_OpenEx(
                self.lastConnectedSerialNumber, 1, ctypes.byref(self.ftHandle)
            )
        )

        eeprom = self.EEPROMData()
        if eeprom is None:
            raise RuntimeError(
                f"Failed to retrieve EEPROM data from the device (SN: {self.lastConnectedSerialNumber}, Description: {self.__SelectedDeviceNode.Description})"
            )
        manufacturer = ctypes.cast(eeprom.Manufacturer, ctypes.c_char_p)
        if manufacturer.value.decode("ascii").upper() == "SANTEC":
            self.__initialize()

    def __initialize(self):
        wordlen = ctypes.c_ubyte(8)
        stopbits = ctypes.c_ubyte(0)
        parity = ctypes.c_ubyte(0)
        FTD2XXHelper.__check(
            self.d2xx.FT_SetDataCharacteristics(
                self.ftHandle, wordlen, stopbits, parity
            )
        )
        flowControl = ctypes.c_uint16(0x00)
        xon = ctypes.c_ubyte(17)
        xoff = ctypes.c_ubyte(19)
        FTD2XXHelper.__check(
            self.d2xx.FT_SetFlowControl(self.ftHandle, flowControl, xon, xoff)
        )
        baudrate = ctypes.c_uint64(9600)
        FTD2XXHelper.__check(self.d2xx.FT_SetBaudRate(self.ftHandle, baudrate))
        timeout = ctypes.c_uint64(1000)
        FTD2XXHelper.__check(self.d2xx.FT_SetTimeouts(self.ftHandle, timeout, timeout))
        mask = ctypes.c_ubyte(0x00)
        enable = ctypes.c_ubyte(0x40)
        FTD2XXHelper.__check(self.d2xx.FT_SetBitMode(self.ftHandle, mask, enable))

    def OpenUsbConnection(self):
        self.initialize()

    def CloseUsbConnection(self):
        if self.ftHandle is not None:
            self.d2xx.FT_Close(self.ftHandle)
            self.ftHandle = None

    def Disconnect(self):
        self.CloseUsbConnection()

    def Write(self, command: str):
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
            FTD2XXHelper.__check(
                self.d2xx.FT_OpenEx(
                    self.lastConnectedSerialNumber, 1, ctypes.byref(self.ftHandle)
                )
            )

        written = ctypes.c_uint()
        commandLen = len(command)
        cmd = (ctypes.c_ubyte * commandLen).from_buffer_copy(command.encode("ascii"))
        FTD2XXHelper.__check(
            self.d2xx.FT_Write(self.ftHandle, cmd, commandLen, ctypes.byref(written))
        )
        time.sleep(0.020)

    def Read(self, maxTimeToWait: float = 0.020, totalNumberOfBytesToRead: int = 0):
        if self.ftHandle is None:
            self.ftHandle = ctypes.c_void_p()
            FTD2XXHelper.__check(
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
            FTD2XXHelper.__check(
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
            FTD2XXHelper.__check(
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

        self.CloseUsbConnection()
        return binaryData

    def QueryIdn(self):
        return self.Query("*IDN?")

    def Query(self, command: str, waitTime: int = 1):
        if self.ftHandle is None:
            self.ftHandle = ctypes.c_void_p()
            FTD2XXHelper.__check(
                self.d2xx.FT_OpenEx(
                    self.lastConnectedSerialNumber, 1, ctypes.byref(self.ftHandle)
                )
            )

        self.Write(command)

        arr = self.Read(waitTime)

        string = ""
        try:
            string = arr.decode("ascii")
        except UnicodeDecodeError:
            print(arr)
            return string

        if len(string) < 3:
            return string.strip()
        elif string[0] == "\0":
            return string

        trimmed = self.__RemovePrefixFromResultIfNotHex(string.strip())

        try:
            idx = trimmed.rindex(self.terminator)
            if len(trimmed) - 2 > idx:
                trimmed = trimmed[(idx + 1):].strip()
        except ValueError:
            pass

        if trimmed == string.strip():
            return trimmed

        return string

    @staticmethod
    def __RemovePrefixFromResultIfNotHex(self, string: str):
        if string is None or len(string) < 3:
            return string

        if string[0] == "\0":
            return string

        if string[0] not in string.hexdigits or string[1] not in string.hexdigits:
            return string[2:]

        return string

    def GetAllDatPointsFromLastScan_SCPICommand(self):
        getCountCommand = "READout:POINts?"
        getDataCommand = "READout:DATa?"

        points = 0
        str = self.Query(getCountCommand)
        print(str)
        try:
            points = int(str)
        except ValueError:
            raise RuntimeError(
                f"Failed to retrieve a valid number of data points from the last scan: {str}"
            )

        if points > 200001:
            raise ValueError(
                f"The number of data points received from the last scan is too large: {points}"
            )

        self.Write(getDataCommand)
        time.sleep(5)
        arr = self.Read(1, points * 4)
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
        except:
            print(arr[1], b)
            raise ValueError(
                f"The value read was supposed to contain a number as the second byte, but contained '{b}'"
            )

        b = "".join(map(chr, arr[2: 2 + val]))
        try:
            num = int(b)
        except:
            print(arr[2: 2 + val], b)
            raise ValueError(
                f"The value read was supposed to contain a number, but contained '{b}'"
            )

        offset = 2 + val
        return list(
            map(
                lambda x: struct.unpack(">f", x),
                FTD2XXHelper.__chunks(arr[offset:], num, 4),
            )
        )

    def GetAllDataPointsFromLastScan_SantecCommand(self):
        getCountCommand = "TN"
        getDataCommand = "TA"

        points = int(self.Query(getCountCommand))

        self.Write(getDataCommand)
        arr = self.Read(1, points * 4)

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
                FTD2XXHelper.__chunks(arr, points, 4),
            )
        )

    @staticmethod
    def __chunks(arr: bytearray, length: int, n: int = 4):
        for i in range(0, length):
            yield arr[i * n: i * n + n]


if __name__ == "__main__":
    devices = FTD2XXHelper.ListDevices()
    print(devices)

    for dev in devices:
        print(dev)
        print(dev.Description)
        print(dev.SerialNumber)

    # # TSL instrument control below
    # tsl = FTD2XXHelper("23110067")
    # print(tsl.QueryIdn())
    # print(tsl)

    # # Perform sweep operation
    # opc = tsl.Query('*OPC?')
    # # print(opc)
    # while opc == 0:
    #     opc = tsl.Query('*OPC?')
    # tsl.Write('TRIG:INP:STAN 1')  # Sets TSL in standby mode (executes only one sweep)
    # tsl.Write('WAV:SWE 1')  # TSL Sweep Status to start
    # opc = 0
    # time.sleep(0.05)
    # while opc == 0:
    #     opc = tsl.Query('*OPC?')
    # check2 = tsl.Query('WAV:SWE?')
    #
    # while check2 != '3':
    #     check2 = tsl.Query('WAV:SWE?')
    #     time.sleep(0.05)
    # tsl.Write('WAV:SWE:SOFT')  # Issues Soft Trigger

    # for tsl in devices:
    #     helper = FTD2XXHelper(tsl.SerialNumber)
    #
    #     helper.Query("*RST")
    #     helper.Query("*CLS")
    #
    #     var = helper.QueryIdn()
    #     print(var)
    #
    #     # print(helper.Query("AO"))
    #     # print(helper.Query("AT5"))
    #     # print(helper.Query("AO"))
    #     # input()
    #     # print(helper.Query("AF"))
    #     # print(helper.Query("LP3"))
    #     # print(helper.Query("AF"))
    #     # input()
    #     # print(helper.Query("AF"))
    #     # print(helper.Query("OP5"))
    #     # print(helper.Query("AF"))
    #     # input()
    #     # print(helper.Query("AO"))
    #     # print(helper.Query("AT10"))
    #     # print(helper.Query("AO"))
    #
    #     print(helper.Query("SO"))
    #     print(helper.Query("AF"))
    #     print(helper.Query("OP5"))
    #     print(helper.Query("WA1575.0"))
    #     print(helper.Query("SS1575.0"))
    #     print(helper.Query("SE1625.0"))
    #     print(helper.Query("WW0.1"))
    #     print(helper.Query("SZ1"))
    #     print(helper.Query("SN5"))
    #     print(helper.Query("SM1"))
    #     var = int(helper.Query("SK"))
    #     print(f"SK: {var}")
    #     if var == 0:
    #         helper.Query("SG")
    #     elif var == 1 or var == 2:
    #         print(helper.Query("SQ"))
    #
    #     var = int(helper.Query("SK"))
    #     print(f"SK: {var}")
    #     while var == 1 or var == 4:
    #         time.sleep(1)
    #         var = int(helper.Query("SK"))
    #         print(f"SK: {var}")
    #
    #     print(helper.Query("SC"))
    #
    #     print(helper.GetAllDataPointsFromLastScan_SantecCommand())
    #
    #     helper.CloseUsbConnection()
    #     break
