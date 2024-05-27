#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import threading
import paramiko
import atexit
import sys
from queue import Queue

ftp_server = ''
ssh_user = 'user'
ssh_password = 'user'

NUM_THREADS = 1 # Set the number of threads to 4 (you can customize)

my_file = open("ip_host.txt"|
ip_queue = Queue()

buff = ''
resp = ''

print (f'Starting the backup...')
print (f'   User: {ssh_user}'
print (f'-----------------------------------------\n')

# List to store information about unmade copies 
niewykonane_kopie = []

def Tftp_Backup():
    while True:
        IP = ip_queue.get()
        try:
            ssh = paramiko.SSHClient()

            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(IP, username=f'{ssh_user}', password=f'{ssh_password}')
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            chan = ssh.invoke_shell()
            chan.settimeout(10)

            print(f"Connected to: {IP}. Starting a backup...")

            chan.send('terminal lenght 0\n')
            time.sleep(1)
            
            tftp_command = f'copy running-config tftp://:{ftp_server}\n'
            chan.send(tftp_command)   
            time.sleep(1)
            chan.send('\r\n')
            time.sleep(1)
            chan.send('\r\n')
            time.sleep(1)
            buff = ''
            
            while buff.find('copied') < 0:
                resp = chan.recv(9999).decode('utf-8')
                buff += resp

            chan.send('exit\n') 
            print(f"\nBackup done {IP}. Disconnecting...")
            ssh.close()

            
        except paramiko.ssh_exception.SSHException as ssh_error:
            print(f"\nSSH error while copying device {IP}: {str(ssh_error)}")
            niewykonane_kopie.append(IP)

        except Exception as e:
            print(f"Another error when copying device {IP}: {str(e)}")
            niewykonane_kopie.append(IP)
            
        finally:
            ip_queue.task_done()

def close_program():
    global program_zamykany
    if not program_zamykany:
        program_zamykany = True
        print("\n------------------------------------------------------")
        my_file.close()

        #Check whether all expected backups have been completed
        if len(niewykonane_kopie) == ip_queue.qsize():
            print("[OK] All backups have been completed successfully.")
        else:
            print("\n[Warning!] Not all backups completed successfully!)
            print("\nDevice copies not made: ")
            for device in niewykonane_kopie:
                print(device)
                
        while True:
            answer = input("\nYou can end the program by pressing Ctrl+C.").strip().lower()
            
if __name__ == "__main__":
    program_zamykany = False
    
    for i in range(NUM_THREADS):
        t = threading.Thread(target=Tftp_Backup)
        t.daemon = True
        t.start()

    for line in my_file:
        l = [i.strip() for i in line.split()]
        IP = l[0]
        ip_queue.put(IP)

    atexit.register(close_program)

    ip_queue.join()
    time.sleep(1)