# AddRunning
# INDIQUER QUE LE SCRIPT EST EN COURS

def main(script_num, running_file_name):
    if script_num == '#1#':
        script_num = 1
    print('running_file_name', running_file_name)
    get_running_file = open(running_file_name + ".txt", "a")
    get_running_file.write(str(script_num))
    get_running_file.close()
