
<p align="right"> <a href="https://www.santec.com/jp/" target="_blank" rel="noreferrer"> <img src="https://www.santec.com/dcms_media/image/common_logo01.png" alt="santec" 
  width="250" height="45"/> </a> </p>

<h1 align="left"> Python FTDI </h1>
Python script for controlling Santec instruments via a USB connection. <br><br>

<h2>Usage</h2>

1) Import the Ftd2xxhelper class from ftd2xxhelper,
   ```python
   from ftd2xxhelper import Ftd2xxhelper
   ```
2) Call the list_devices method,
   ```python
   list_of_devices = Ftd2xxhelper.list_devices()      # Gets the list of detected USB connections
   ```
    
3) Print the description and serial number of each detected device,
   ```python
   for device in list_of_devices:
      print(device.Description)
      print(device.SerialNumber)
   ```          
   
4) Creating a device control instance / object,
   ```python   
   device = Ftd2xxhelper(list_of_devices[0].SerialNumber)
   
   (or)
       
   serial_number = str(MY_SERIAL_NUMBER).encode('utf-8')      # Here, MY_SERIAL_NUMBER is the Serial number of the instrument, Example = 23110980, 21862492
   device = Ftd2xxhelper(serial_number)
   ```    

5) Print the device identification string,
   ```python
   idn_query = device.query_idn()     
   print(idn_query)       # Output: SANTEC TSL-570, 23119807, 0029.0067.0001
   ```

6) Write a command,
   ```python
   device.write('YOUR_COMMAND')      # Refer to the instrument manual for commands
   ```

7) Query a command,
   ```python
   result = device.query('YOUR_COMMAND')      # Refer to the instrument manual for commands
   print(result)
   
   ```
   ❗If the query() method is not functional, you can instead use the write() method followed by calling the read() method, as shown below,
   ```python
   device.write('YOUR_COMMAND')      # Refer to the instrument manual for commands
   result = device.read()              
   print(result)
   ```   
  
8) Disposing the usb connection after use.
   ```python
   device.close_usb_connection()
   ```
   
