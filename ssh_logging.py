from pydoc import cli
import paramiko
import csv, time

class remote_logging:
    def __init__(self):
        # Try to ssh into the remote computer and create a client object with default parameters
        self.connect()
        self.latest_timestamp = ""
        self.latest_shotno = ""
        pass

    def connect(self, hostname="192.168.130.25", username="wham", password="P@th2Fusion"):
        # Default credentials are for Michael, the LabView PC
        client = paramiko.SSHClient()
        # SSH connection over local network
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, password=password)
        self.client = client
        return client

    def open_remote_file(self, filename):
        sftp_client = self.client.open_sftp()
        file = sftp_client.open(filename)
        return file

    def read_michael_data(self, filename="/mnt/c/Users/WHAMuser/Documents/Data Logging/Control_System_Data.csv"):
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
        
        # We start at the 3rd column because the first two is presumed to be date and time
        n = 2
        # Only log the data that are populated in the last row of the file
        while n < len(last_row):
            data_field_name = header[n].replace(" ", "")
            latest_data.append("LabView_Log,sensor=" + data_field_name + " data_field={:}".format(float(last_row[n])))
            n += 1

        time.sleep(10)
        # Check the latest timestamp, if it is the same as the last timestamp, don't send it to the DB
        if last_row[1] == self.latest_timestamp:
            return 0
        elif self.latest_timestamp == "":
            self.latest_timestamp = last_row[1]
            return 0
        else:
            self.latest_timestamp = last_row[1]
            print(latest_data)
            return latest_data
    
    def read_shot_data(self, filename="/mnt/c/Users/WHAMuser/Documents/Data Logging/shot_data.csv"):
        # This function reads the latest shot number and other set point data
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
            return None

        n = 0
        # Skipping over the very last column for now, it's an error message log
        while n < len(last_row)-1:
            data_field_name = header[n].replace(" ", "")
            latest_data.append("ShotData_Log,sensor=" + data_field_name + " data_field={:}".format(float(last_row[n])))
            n += 1
        
        # Check the latest shot number, if it is the same as the last shot number, don't send it to the DB
        if last_row[0] == self.latest_shotno:
            time.sleep(10)
            return 0
        else:
            self.latest_shotno = last_row[0]
            time.sleep(10)
            print(latest_data)
            return latest_data