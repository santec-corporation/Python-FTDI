# -*- coding: utf-8 -*-
# !/usr/bin/env python

"""
Santec Python FTDI
This is an example usage program.

@organization: santec holdings corp.
"""

# Import the ftd2xxhelper file
import ftd2xxhelper as ftd2


""" Example Usage """
devices = ftd2.FTD2XXHelper.ListDevices()
print(devices)

for dev in devices:
    print(dev)
    print(dev.Description)
    print(dev.SerialNumber)

""" TSL instrument control below """
tsl = ftd2.FTD2XXHelper("23110067")
print(tsl.QueryIdn())
print(tsl)

""" Perform sweep operation (TSL-570) (SCPI commands)"""
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


""" TSL test commands (TSL-550) (Santec commands)"""
# for tsl in devices:
#     helper = ftd2.FTD2XXHelper(tsl.SerialNumber)
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
