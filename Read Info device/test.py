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
f = open("IOS.csv", "w+")
f.write("IP Address;Hostname;Uptime;Current_Version;Current_Image;Serial_Number;Device_Model;Device_Memory;Device_Time;SSH_Version;NTP_Status;STP_Mode")
f.write("\n")
f.close()

#clearing the old data from the CSV file and writing the headers
print(f"login_issues.csv")
f = open("login_issues.csv", "w+")
f.write("IP Address;Status")
f.write("\n")
f.close()

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
        f = open("login_issues.csv", "a")
        f.write(ip + ";" + "Device Unreachable/SSH not enabled")
        f.write("\n")
        f.close()
        continue
    except AuthenticationException:
        f = open("login_issues.csv", "a")
        f.write(ip + ";" + "Authentication Failure")
        f.write("\n")
        f.close()
        continue
    except SSHException:
        f = open("login_issues.csv", "a")
        f.write(ip + ";" + "SSH not enabled")
        f.write("\n")
        f.close()
        continue

    try:
        net_connect.enable()

    #handling exceptions errors        
    except ValueError:
        f = open("login_issues.csv", "a")
        f.write(ip + ";" + "Could be SSH Enable Password issue")
        f.write("\n")
        f.close()
        continue
    
    print(f"Connected to {ip}. Reading data...")

    net_connect.send_command('terminal length 0')
    sh_ver_output = net_connect.send_command('show version')
    sh_clock_output = net_connect.send_command('show clock')  # Get the current time on the device
    sh_ssh_output = net_connect.send_command('show ip ssh')  # Get SSH version information
    sh_ntp_output = net_connect.send_command('show ntp status')  # Get NTP status information
    sh_stp_output = net_connect.send_command('show spanning-tree')  # Get STP mode information

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

    # Append results to table [hostname, uptime, version, serial, ios, model, memory, device_time, ssh_version, ntp_status, stp_mode]
    devices.append([ip, hostname, uptime, version, ios, serial, model, memory, device_time, ssh_version, ntp_status, stp_mode])

    print(f"Data read from {ip}. Disconnecting...")
    net_connect.disconnect()
    
#print all results (for all routers) on screen    
with open ("IOS.csv", "a") as f:
    for device in devices:
        f.write(";".join(device) + "\n")

print(f"All connections closed and data saved")
