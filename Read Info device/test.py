from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException
from netmiko.exceptions import SSHException
from netmiko.exceptions import AuthenticationException

import re
import time

#here is list of cisco routers ip addresses
def read_ip_list(file_path):
    with open(file_path, 'r') as file:
        ip_list = [line.strip() for line in file if line.strip()]
    return ip_list

ip_list = read_ip_list('ip_list.txt')

#list where informations will be stored
devices = []

#clearing the old data from the CSV file and writing the headers
print(f"Create file IOS.csv")
with open("IOS.csv", "w+") as f:
    f.write("IP Address;Hostname;Uptime;Current_Version;Current_Image;Serial_Number;Device_Model;Device_Memory;Device_Time;SSH_Version;NTP_Status;STP_Mode;Power_Supplies;Stack_Members\n")

#clearing the old data from the CSV file and writing the headers
print(f"Create file login_issues.csv")
with open("login_issues.csv", "w+") as f:
    f.write("IP Address;Status\n")

#loop all ip addresses in ip_list
for ip in ip_list:
    cisco = {
    'device_type':'autodetect',
    'ip':ip,
    'username':'cisco',     #ssh username
    'password':'cisco',  #ssh password
    'ssh_strict':False,  
    'fast_cli':False,
    }
    
    #handling exceptions errors
    try:
        net_connect = ConnectHandler(**cisco)
    except NetMikoTimeoutException:
        with open("login_issues.csv", "a") as f:
            f.write(ip + ";" + "Device Unreachable/SSH not enabled\n")
        continue
    except AuthenticationException:
        with open("login_issues.csv", "a") as f:
            f.write(ip + ";" + "Authentication Failure\n")
        continue
    except SSHException:
        with open("login_issues.csv", "a") as f:
            f.write(ip + ";" + "SSH not enabled\n")
        continue

    try:
        net_connect.enable()
    #handling exceptions errors        
    except ValueError:
        with open("login_issues.csv", "a") as f:
            f.write(ip + ";" + "Could be SSH Enable Password issue\n")
        continue
    
    print(f"Connected to {ip}. Reading data...")

    net_connect.send_command('terminal length 0')
    sh_ver_output = net_connect.send_command('show version')
    sh_clock_output = net_connect.send_command('show clock')  # Get the current time on the device
    sh_ssh_output = net_connect.send_command('show ip ssh')  # Get SSH version information
    sh_ntp_output = net_connect.send_command('show ntp status')  # Get NTP status information
    sh_stp_output = net_connect.send_command('show spanning-tree')  # Get STP mode information
    sh_inv_output = net_connect.send_command('show inventory')  # Get inventory information including power supplies
    sh_stack_output = net_connect.send_command('show switch detail')  # Get stack information

    output_lines = sh_ver_output.split('\n')

    hostname = None
    uptime = None
    version = None
    serial = None
    ios = None
    model = None
    memory = None
    device_time = None  # Variable for storing device time
    ssh_version = None  # Variable for storing SSH version
    ntp_status = None  # Variable for storing NTP status
    stp_mode = None  # Variable for storing STP mode
    power_supplies = []  # List for storing power supply information
    stack_members = 0  # Variable for storing number of stack members

    for line in output_lines:
        if ' uptime is ' in line:
            hostname = line.split(' ')[0]
            uptime = line.split(' uptime is ')[1]
            uptime = uptime.replace(',' ,'').replace("'" ,"")
            uptime = uptime.strip()
        if 'Cisco IOS Software' in line:
            version = line.split('Version ')[1].split(',')[0]
        if 'Processor board ID' in line:
            serial = line.split(' ')[-1]
        if 'System image file is' in line:
            ios = line.split('"')[1]
        if line.lower().startswith('cisco') and 'memory' in line:
            model = line.split(' ')[1]
        if 'with' in line and 'bytes of memory' in line:
            memory = line.split('with ')[1].split(' bytes')[0]

    # Extract device time from 'show clock' output
    device_time = sh_clock_output.strip()

    # Extract SSH version from 'show ip ssh' output
    ssh_lines = sh_ssh_output.split('\n')
    for line in ssh_lines:
        if 'SSH' in line and 'version' in line:
            ssh_version = line.strip()
            break

    # Extract NTP status from 'show ntp status' output
    ntp_lines = sh_ntp_output.split('\n')
    for line in ntp_lines:
        if 'Clock is synchronized' in line:
            ntp_status = "synchronized"
            break
        elif 'Clock is unsynchronized' in line:
            ntp_status = "unsynchronized"
            break

    # Extract STP mode from 'show spanning-tree' output
    stp_lines = sh_stp_output.split('\n')
    for line in stp_lines:
        if 'Switch is in rapid-pvst mode' in line:
            stp_mode = "rapid-pvst"
            break
        elif 'Switch is in pvst mode' in line:
            stp_mode = "pvst"
            break

    # Extract power supplies information from 'show inventory' output
    inv_lines = sh_inv_output.split('\n')
    for line in inv_lines:
        if 'POWER SUPPLY' in line.upper():
            power_supplies.append(line.strip())

    # Convert power supplies list to a string
    power_supplies_str = ', '.join(power_supplies) if power_supplies else 'No power supplies found'

    # Extract stack member count from 'show switch detail' output
    stack_lines = sh_stack_output.split('\n')
    for line in stack_lines:
        if 'Switch' in line and 'Role' in line:
            stack_members += 1

    # Ensure all elements are strings before appending to devices list
    devices.append([str(ip), str(hostname), str(uptime), str(version), str(ios), str(serial), str(model), str(memory), str(device_time), str(ssh_version), str(ntp_status), str(stp_mode), power_supplies_str, str(stack_members)])

    print(f"Data read from {ip}. Disconnecting...")
    net_connect.disconnect()
    
#print all results (for all routers) on screen    
with open ("IOS.csv", "a") as f:
    for device in devices:
        f.write(";".join(device) + "\n")

print(f"All connections closed and data saved")
