from flask import Flask, render_template, Response, request, render_template_string, send_file
import time
import json
import connections
import constants
import camera
import shared

import os

app = Flask(__name__, static_url_path='/static')
shared.purge_old_lines()

##To do
##camera API for CRUD - list, get_file, delete
###when not connected, show local filelist only
###button to indicate whether it downloaded or not
###delete button

@app.route('/', methods=['GET'])
def index():
    mode = request.args.get('mode')
    if mode != "photo":
        mode = "movie"

    connectivity = connections.check_connectivity(constants.camera['camera_ip'],3)
    return render_template('index.html', mode=mode, connectivity=connectivity['status'])

@app.route('/connect', methods=['GET', 'POST'])
def connect():
    #check if camera can be reached
    connectivity_result = connections.check_connectivity(constants.camera['camera_ip'],4)
    if connectivity_result['status'] == 'OK':
        shared.log_message(connectivity_result)
        return json.dumps(connectivity_result) + "\n"
    else: ##connect to camera
        return Response(connections.connect_sequence(constants.camera['camera_ip'], constants.camera['camera_wifi_prefix'],constants.camera['camera_wifi_password'], constants.camera['camera_bluetooth_id'],constants.camera['camera_bluetooth_service_id'],constants.camera['camera_bluetooth_characteristic_id']), mimetype='text/event-stream')

@app.route('/disconnect')
def disconnect():
    shared.log_message("Attempting to disconnect")
    getSSID = connections.getSSID(constants.camera['camera_wifi_prefix'])
    disconnection_status = connections.disconnect_wifi(getSSID['targetSSID'],constants.camera['camera_ip'] )
    return json.dumps(disconnection_status) + "\n"

@app.route('/list')
def list():
    mode = request.args.get('mode')
    display_list = []

    local_list = camera.get_local_files(mode)
    remote_list = camera.remote_list(constants.camera['camera_ip'], mode)

    for remote_file in remote_list['file_list'][:]:
        for local_file in local_list[:]:
            if remote_file['timestamp'] == local_file['timestamp']:
               remote_file['actions'] = ['delete-local', 'delete-remote','view']
               remote_file['name'] = local_file['name']
               local_list.remove(local_file)

    display_list = local_list + remote_list['file_list']
    display_list = sorted(display_list, key=lambda d: float('-inf') if d['date'] is None else d['date'])

    actions_buttons = {
        'delete-local':'<input type="button" class="delete" onclick=\'delete_media("local","#filename#","#filetype#");\' value="Delete Local"/>',
        'delete-remote':'<input type="button" class="delete" onclick=\'delete_media("remote","#filename#","#filetype#");\' value="Delete Remote"/>',
        'view':'<a href="/view?filename=#filename#&filetype=#filetype#"><input type="button" class="view"value="View"/></a>',
        'download': '<a href="/download?filename=#filename#&filetype=#filetype#&filetime=#filetime#"><input type="button" class="download"value="Download"/></a>'
    }

    for element_index, element in enumerate(display_list):
        for action_index, action in enumerate(display_list[element_index]['actions']):
            for key, value in actions_buttons.items():
                if key == action:
                    display_list[element_index]['actions'][action_index] = value\
                        .replace("#filename#",str(display_list[element_index]['name']))\
                        .replace("#filetype#",str(display_list[element_index]['type']))\
                        .replace("#filetime#",str(display_list[element_index]['timestamp']))
            
    return render_template('list.html', records=display_list, colnames=['name','date','actions'])

@app.route('/delete', methods=['GET'])
def delete():
    location = request.args.get('location')
    filetype = request.args.get('filetype')
    filename = request.args.get('filename')

    if location == 'local':
        delete_repsonse = camera.delete_local(filename,filetype)
    elif location == 'remote':
        delete_repsonse = camera.delete_remote(constants.camera['camera_ip'],filename,filetype)

    return(delete_repsonse)

@app.route('/view',methods=['GET'])
def view():
    filename = request.args.get('filename')
    filetype = request.args.get('filetype')

    filelocation = 'static/'+filetype+'/'+filename

    dictionary = {"photo":"image/png", "movie":"video/mp4" } 
    for key in dictionary.keys():
        filetype = filetype.replace(key, dictionary[key])

    return send_file(filelocation,filetype)

@app.route('/download', methods=['GET'])
def copy_file():
    filename = request.args.get('filename')
    filetype = request.args.get('filetype')
    filetime = request.args.get('filetime')

    copy_response = camera.copy_file(constants.camera['camera_ip'],filename, filetype, filetime)

    dictionary = {"photo":"image/png", "movie":"video/mp4" } 
    for key in dictionary.keys():
        filetype = filetype.replace(key, dictionary[key])

    if copy_response['status'] == 'OK':
        return send_file(copy_response['filelocation'],filetype)
    else:
        return render_template_string('Error')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')