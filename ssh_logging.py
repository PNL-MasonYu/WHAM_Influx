from pydoc import cli
import paramiko
import csv

class remote_logging:
    def __init__(self):
        pass

    def connect(self, hostname="192.168.130.25", username="wham", password="P@th2Fusion"):
        client = paramiko.SSHClient()
        client.load_host_keys()
        client.connect(hostname, username=username, password=password)
        return client

    def open_remote_file(self, ssh_client, filename):
        sftp_client = ssh_client.open_sftp()
        file = sftp_client.open(filename)
        return file

    def read_michael_data(self, filename="/mnt/c/Users\WHAMuser\Documents\Data Logging\Control_System_Data.csv"):
        # This function reads the LabView Data logged on Michael
        # It only reads the latest data, and will return a command for upload onto InfluxDB
        file = self.open_remote_file(filename)
        csvreader = csv.reader(file)
        latest_data = []
        line_count = 0
        for row in csvreader:
            if line_count == 0:
                header = row
            last_row = row
            line_count += 1
        if line_count > 1e6:
            # TO DO: Replace the file if it gets too big
            pass
        n = 0
        for data_field_name in header:
            data_field_name.replace(" ", "")
            latest_data.append("LabView_Log,sensor=" + data_field_name + "data_field={:}".format(last_row[n]))
            n += 1
        print(header)
        print(latest_data)
        return
            