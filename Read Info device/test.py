from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, AuthenticationException, SSHException

def read_ip_list(file_path):
    with open(file_path, 'r') as file:
        ip_list = [line.strip() for line in file if line.strip()]
    return ip_list

ip_list = read_ip_list('ip_list.txt')

# Create and initialize the CSV files with headers
print(f"Create file IOS.csv")
with open("IOS.csv", "w+") as f:
    f.write("IP Address;Hostname;Uptime;Current_Version;Current_Image;Serial_Number;Device_Model;Device_Memory;Device_Time;SSH_Version;NTP_Status;STP_Mode;Switch_Stack\n")

print(f"Create file login_issues.csv")
with open("login_issues.csv", "w+") as f:
    f.write("IP Address;Status\n")

# Loop through each IP in the list
for ip in ip_list:
    cisco = {
        'device_type': 'autodetect',
        'ip': ip,
        'username': 'cisco',
        'password': 'cisco',
        'ssh_strict': False,
        'fast_cli': False,
    }

    try:
        net_connect = ConnectHandler(**cisco)
    except NetMikoTimeoutException:
        with open("login_issues.csv", "a") as f:
            f.write(ip + ";Device Unreachable/SSH not enabled\n")
        continue
    except AuthenticationException:
        with open("login_issues.csv", "a") as f:
            f.write(ip + ";Authentication Failure\n")
        continue
    except SSHException:
        with open("login_issues.csv", "a") as f:
            f.write(ip + ";SSH not enabled\n")
        continue

    print(f"Connected to {ip}. Reading data...")
    net_connect.send_command('terminal length 0')

    # Extract data from the device
    sh_ver_output = net_connect.send_command('show version')
    sh_clock_output = net2_connect.send_command('show clock')
    sh_ssh_output = net_connect.send_command('show ip ssh')
    sh_ntp_output = net_connect.send_command('show ntp status')
    sh_stp_output = net_connect.send_command('show spanning-tree summary')
    sh_switch_output = net_connect.send_command('show switch')

    # Count Active and Standby switches
    active_count = len([line for line in sh_switch_output.split('\n') if 'Active' in line])
    standby_count = len([line for line in sh_switch_output.split('\n') if 'Standby' in one])

    # Combine Active and Standby counts into one string
    switch_stack = f"Active: {active_count}, Standby: {standby_count}"

    # Process other command outputs as before
    hostname, uptime, version, ios, serial, model, memory = None, None, None, None, None, None, None
    ssh_version, ntp_status, stp_mode = None, None, None
    for line in sh_ver_output.split('\n'):
        # extract various fields from sh_ver_output
        # (similar to the original script processing)

    devices.append([str(ip), str(hostname), str(uptime), str(version), str(ios), str(serial), str(model), str(memory), str(device_time), str(ssh_version), str(ntp_status), str(stp_mode), switch_stack])

    print(f"Data read from {ip}. Disconnecting...")
    net_connect.disconnect()

# Save all data to the CSV file
with open ("IOS.csv", "a") as f:
    for device in devices:
        f.write(";".join(device) + "\n")

print(f"All connections closed and data saved")
