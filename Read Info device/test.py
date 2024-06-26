from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, SSHException, AuthenticationException
import re
import time

# Function to read the list of IP addresses from a file
def read_ip_list(file_path):
    with open(file_path, 'r') as file:
        ip_list = [line.strip() for line in file if line.strip()]
    return ip_list

ip_list = read_ip_list('ip_list.txt')

# List where information will be stored
devices = []

# Clear the old data from the CSV file and write the headers
print(f"Create file IOS.csv")
with open("IOS.csv", "w+") as f:
    f.write("IP Address;Hostname;Device_Model;Serial_Number;Current_Version;Uptime;Device_Time;NTP_Status;STP_Mode;SSH_Version;Device_Memory;Current_Image;Power_Supplies;Matching_Lines\n")

print(f"Create file login_issues.csv")
with open("login_issues.csv", "w+") as f:
    f.write("IP Address;Status\n")

# Loop through all IP addresses in ip_list
for ip in ip_list:
    cisco = {
        'device_type': 'autodetect',
        'ip': ip,
        'username': 'cisco',     # SSH username
        'password': 'cisco',     # SSH password
        'ssh_strict': False,
        'fast_cli': False,
    }

    # Handling exceptions for connection errors
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
    sh_stp_output = net_connect.send_command('show spanning-tree summary')  # Get STP mode information
    sh_inv_output = net_connect.send_command('show inventory')  # Get stack information

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
    matching_lines = []  # List for storing lines that match any serial number

    for line in output_lines:
        if ' uptime is ' in line:
            hostname = line.split(' ')[0]
            uptime = line.split(' uptime is ')[1]
            uptime = uptime.replace(',', '').replace("'", "")
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
        if 'System serial number' in line:
            matching_lines.append(line.strip())

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
            ntp_status = "[OK] synchronized"
            break
        elif 'Clock is unsynchronized' in line:
            ntp_status = "[BAD!] unsynchronized"
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

    inv_lines = sh_inv_output.split('\n')
    for line in inv_lines:
        if 'POWER SUPPLY' in line.upper():
            power_supplies.append(line.strip())

    # Convert power supplies list to a string
    power_supplies_str = ', '.join(power_supplies) if power_supplies else 'Built-in power supply'

    # Ensure all elements are strings before appending to devices list
    devices.append([str(ip), str(hostname), str(model), str(serial), str(uptime), str(version), str(uptime), str(device_time), str(ntp_status), str(stp_mode), str(ssh_version), str(memory), str(ios), str(power_supplies_str), ', '.join(matching_lines)])

    print(f"Data read from {ip}. Disconnecting...")
    net_connect.disconnect()

# Print all results (for all routers) on screen and save to CSV
with open("IOS.csv", "a") as f:
    for device in devices:
        f.write(";".join(device) + "\n")

print(f"All connections closed and data saved")
