from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException, SSHException, AuthenticationException
import re

# Odczytaj listę adresów IP z pliku
def read_ip_list(file_path):
    with open(file_path, 'r') as file:
        ip_list = [line.strip() for line in file if line.strip()]
    return ip_list

ip_list = read_ip_list('ip_list.txt')

# Lista, w której będą przechowywane informacje o urządzeniach
devices = []

# Utwórz plik IOS.csv i zapisz nagłówki
with open("IOS.csv", "w+") as f:
    f.write("IP Address;Active_Standby_Lines\n")

# Loop przez wszystkie adresy IP w liście
for ip in ip_list:
    cisco = {
        'device_type': 'autodetect',
        'ip': ip,
        'username': 'cisco',     # nazwa użytkownika SSH
        'password': 'cisco',     # hasło SSH
        'ssh_strict': False,
        'fast_cli': False,
    }

    # Obsługa wyjątków
    try:
        net_connect = ConnectHandler(**cisco)
    except (NetMikoTimeoutException, AuthenticationException, SSHException) as e:
        # Zapisz wyjątek do pliku login_issues.csv
        with open("login_issues.csv", "a") as f:
            f.write(f"{ip};{str(e)}\n")
        continue

    try:
        net_connect.enable()
    except ValueError:
        with open("login_issues.csv", "a") as f:
            f.write(f"{ip};Could be SSH Enable Password issue\n")
        continue

    print(f"Connected to {ip}. Reading data...")

    # Pobierz wyjście polecenia show switch
    sh_switch_output = net_connect.send_command("show switch")

    # Zlicz linie ze statusem Active lub Standby
    active_standby_lines = sum(1 for line in sh_switch_output.split("\n") if "Active" in line or "Standby" in line)

    # Dodaj informacje do listy urządzeń
    devices.append([ip, str(active_standby_lines)])

    print(f"Data read from {ip}. Disconnecting...")
    net_connect.disconnect()

# Zapisz informacje do pliku IOS.csv
with open("IOS.csv", "a") as f:
    for device in devices:
        f.write(";".join(device) + "\n")

print("All connections closed and data saved")
