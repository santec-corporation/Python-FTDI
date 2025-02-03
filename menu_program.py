# -*- coding: utf-8 -*-

"""
Python FTDI menu program.

@organization: Santec Holdings Corporation.
"""

import os
import sys
import time

# Import the Ftd2xxhelper class.
from ftd2xxhelper import Ftd2xxhelper

# List of detected devices
list_of_devices = Ftd2xxhelper.list_devices()


# Instrument control class
class Santec:
    def __init__(self, instrument):
        """
        default parameter initialization
        :parameter instrument - user selected instrument instance
        """
        self.instrument: Ftd2xxhelper = instrument

    def query_instrument(self):
        """
         Queries a command to the instrument inputted by the user
        """
        command = input("\nEnter the command to Query (eg. POW ?) ").upper()
        query = self.instrument.query(f'{command}')
        print(query)
        time.sleep(0.25)
        input("\nPress any key to continue...")

        return True

    def write_instrument(self):
        """
        Writes a command to the instrument inputted by the user
        """
        command = input("\nEnter the command to Write (eg. POW 1) ").upper()
        self.instrument.write(f'{command}')
        print("\nCommand written.")
        time.sleep(0.5)

        return True

    def query_idn_instrument(self):
        """
        Instrument identification query
        """
        print(self.instrument.query_idn())
        time.sleep(0.25)
        input("\nPress any key to continue...")
        return True

    def close_connection(self):
        print("\nClosing instrument USB connection...")
        self.instrument.close_usb_connection()

    def goto_main_menu(self):
        self.close_connection()
        time.sleep(0.2)
        main_menu()

    def exit_program(self):
        self.close_connection()
        sys.exit()

    def instrument_menu(self):
        """
        Menu to select Query, Write or QueryIdn to the instrument
        """
        menu = {
            '1': self.query_instrument,
            '2': self.write_instrument,
            '3': self.query_idn_instrument,
            '4': self.goto_main_menu,
            '5': self.exit_program
        }
        while True:
            time.sleep(0.2)
            os.system('cls')
            user_operation = input("\nInstrument Menu:-"                                   
                                   "\n1. Query Instrument"
                                   "\n2. Write Instrument"
                                   "\n3. QueryIdn Instrument"
                                   "\n4. Go to Instrument Connection"
                                   "\n5. Exit"
                                   "\nSelect an operation: "
                                   )

            if user_operation in menu:
                menu[user_operation]()
            else:
                print("\nInvalid selection.....try again.....")


# Main menu to select to instrument
def main_menu():
    """
    Main method
    Display the list of detected Santec USB instruments and select an instrument,
    and initializes the Santec control class
     :parameter
     user_select_instrument_number : Example(instrument serial no.) = 15862492, 17834634, 12862492
    """
    # List to store all the detected instruments
    device_list = []

    # Print the Name and Serial number of each detected instrument
    if not list_of_devices:
        print("\nNo instruments found")
    else:
        print("\nDetected Instruments:-")
        for index, device in enumerate(list_of_devices, start=1):
            if device:
                print(f"\n{index}. Device Name: {device.Description.decode('utf-8')},  "
                      f"Serial Number: {device.SerialNumber.decode('utf-8')}")
                device_list.append(device.SerialNumber.decode('utf-8'))

    # Instrument selection and the control class initialization
    while device_list:
        user_select_instrument_number = (
            input("\nEnter the serial number of the instrument to control (eg. 15862492): "))

        if user_select_instrument_number in device_list:
            serial_number = str(user_select_instrument_number).encode('utf-8')
            instrument = Ftd2xxhelper(serial_number)
            print(f"CONNECTION SUCCESSFUL, CONNECTED TO {instrument.query_idn()}")
            Santec(instrument).instrument_menu()
        else:
            print("\nInvalid serial number.....try again.....")


if __name__ == '__main__':
    main_menu()
