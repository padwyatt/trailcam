import connections
import camera
import constants
import shared
import time
import json

filetype='movie'

shared.log_message("Running scheduled import")
copied_file_counter = 0

*_, connection_status = connections.connect_sequence(constants.camera['camera_ip'], constants.camera['camera_wifi_prefix'],constants.camera['camera_wifi_password'], constants.camera['camera_bluetooth_id'],constants.camera['camera_bluetooth_service_id'],constants.camera['camera_bluetooth_characteristic_id'])


if json.loads(connection_status)['status']=='OK': 
    remote_files = camera.remote_list(constants.camera['camera_ip'],filetype)['file_list']
    local_files = camera.get_local_files(filetype)

    #get a list of all the files that are not on remote but are not local
    for remote_file in remote_files[:]:
        for local_file in local_files[:]:
            if remote_file['timestamp'] == local_file['timestamp']:
                remote_files.remove(remote_file)

    if len(remote_files)>0:
        for remote_file in remote_files:
            copy_status = camera.copy_file(constants.camera['camera_ip'], remote_file['name'], remote_file['type'], remote_file['timestamp'])
            if copy_status['status'] == 'OK':
                copied_file_counter +=1

    message = str(copied_file_counter)+ " new files downloaded"
    shared.log_message(message)

    t_end = time.time() + 60
    disconnection_status = {'status': None}
    while (time.time() < t_end) & (disconnection_status['status'] != 'OK'):
        getSSID = connections.getSSID(constants.camera['camera_wifi_prefix'])
        disconnection_status = connections.disconnect_wifi(getSSID['targetSSID'],constants.camera['camera_ip'] )

else:
    shared.log_message("Failed scheduled run - unable to connect")