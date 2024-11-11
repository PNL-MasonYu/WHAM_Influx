from MDSplus import connection
import time


def read_shot_number(server="andrew.psl.wisc.edu"):

    conn = connection.Connection("andrew.psl.wisc.edu")
    conn.openTree("wham", 0)
    shot_number = conn.get('$shot')
    msg = []
    msg.append("MDSPlus,data=shot shot_n=" + str(shot_number))
    time.sleep(1)
    conn.closeAllTrees()
    
    return msg

if __name__ == "__main__":
    print(read_shot_number())