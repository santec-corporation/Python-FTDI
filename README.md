
<p align="right"> <a href="https://www.santec.com/jp/" target="_blank" rel="noreferrer"> <img src="https://www.santec.com/dcms_media/image/common_logo01.png" alt="santec" 
  width="250" height="45"/> </a> </p>

> [!WARNING]  
> The repo is a work in progress.

> [!CAUTION]
> Do not use this repo for your personal use.

<h1 align="left"> Santec Python FTDI </h1>
Pure python backend script to control Santec instruments via USB. 

<br> 

<h2>Usage</h2>

1) Import the ftd2xxhelper file in your main program,
   ```python
   import ftd2xxhelper
   ```
2) List of detected devices,
   ```python
   list_of_devices = Ftd2xxhelper.list_devices()
   print(list_of_devices)
   ```
    
3) Printing each device's properties,
   ```python
   for device in list_of_devices:
      print(device.Description)
      print(device.SerialNumber)
   ```          
   
4) Creating a device control instance,
   ```python
   # Here parameter is the Serial number of the instrument in result_str format
   device = Ftd2xxhelper("SerialNumber")        # Instrument Serial Number Example = 23110980, 20208978, 21862492
   ```    

5) To get the device identification string,
   ```python
   idn_query = device.query_idn()                 # Output: SANTEC INS-(ModelNumber), SerialNumber, VersionNumber
   print(idn_query)
   ```

6) To write a command,
   ```python
   device.write('command')                       # refer to the instrument datasheet for commands
   ```

7) To query a command,
   ```python
   result = device.query('command')              # refer to the instrument datasheet for commands
   print(result)
   ```
   ❗ If the above method does not work, then instead use the Write() followed by Read() method as shown below,
   ```python
   device.write('command')                       # refer to the instrument datasheet for commands
   result = device.read()            
   print(result)
   ```   
  
8) Closing the device's usb connection after use. Any future commands sent will throw an exception, as the connection is already closed,
   ```python
   device.close_usb_connection()
   ```