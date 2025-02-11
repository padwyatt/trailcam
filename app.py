from flask import Flask, render_template, Response, request, render_template_string
import requests
import time
import json
import connections
from datetime import datetime
from bs4 import BeautifulSoup

import os

app = Flask(__name__, static_url_path='/static')

##To do
###Proper connect/disconnect buttons and status area
###when not connected, show local filelist only
###button to indicate whether it downloaded or not
###delete button

constants = {
    'camera_bluetooth_id':'d6:39:32:33:7c:46',
    'camera_bluetooth_service_id':'0000ffe0-0000-1000-8000-00805f9b34fb',
    'camera_bluetooth_characteristic_id':'0000ffeb-0000-1000-8000-00805f9b34fb',
    'camera_ip':'192.168.8.120',
    'camera_wifi_prefix':'4K WIFI CAM-',
    'camera_wifi_password': '12345678',

}

@app.route('/', methods=['GET'])
def index():
    mode = request.args.get('mode')
    if mode != "photo":
        mode = "movie"

    connectivity = connections.check_connectivity(constants['camera_ip'],5)
    return render_template('index.html', mode=mode, connectivity=connectivity['status'])

@app.route('/connect', methods=['GET', 'POST'])
def connect():

    def connect_sequence():
        status = 'Failed'
        loop = 0
        while (loop <= 3) & (status == 'Failed'):
            loop += 1
            yield json.dumps({'status':'Activating WiFi (attempt '+str(loop)+'/4)'}) + "\n"

            ##check if the network is already broadcasting. If not, activate it
            target_SSID = connections.getSSID(constants['camera_wifi_prefix'])
            if target_SSID['status'] != 'error':
                yield json.dumps({'status':'Wifi Network activated: '+ target_SSID['message']}) + "\n"
                activation_result = connections.connect_wifi(target_SSID['message'], constants['camera_wifi_password'])
            else:
                bluetooth_result = connections.activate_wifi(constants['camera_bluetooth_id'],constants['camera_bluetooth_service_id'],constants['camera_bluetooth_characteristic_id'])
                if bluetooth_result['status'] == 'OK':
                    activation_result = connections.connect_wifi(target_SSID['message'], constants['camera_wifi_password'])
                    yield json.dumps({'status':bluetooth_result['message']}) + "\n"    
                else:
                    activation_result = {'status':'error'}
                    yield json.dumps({'status':bluetooth_result['message']}) + "\n"

            if activation_result['status'] == 'OK':
                yield json.dumps({'status':activation_result['message']}) + "\n"
                connectivity_result = connections.check_connectivity(constants['camera_ip'])
                if connectivity_result['status'] == 'OK':
                    status = connectivity_result['message']

            #if bluetooth_result['status'] == 'OK':
            #    yield json.dumps({'status':bluetooth_result['message']}) + "\n"
            #    target_SSID = connections.getSSID(constants['camera_wifi_prefix'])
            #    if target_SSID['status'] != 'error':
            #        yield json.dumps({'status':'Wifi Network activated: '+ target_SSID['message']}) + "\n"
            #        activation_result = connections.connect_wifi(target_SSID['message'], constants['camera_wifi_password'])
            #        if activation_result['status'] == 'OK':
            #            yield json.dumps({'status':activation_result['message']}) + "\n"
            #            connectivity_result = connections.check_connectivity(constants['camera_ip'])
            #            if connectivity_result['status'] == 'OK':
            #                status = connectivity_result['message']
            #        else:
            #            yield json.dumps({'status':activation_result['message']}) + "\n"
            #    else:
            #        yield json.dumps({'status':target_SSID['message']}) + "\n"    
            #else:
            #    yield json.dumps({'status':bluetooth_result['message']}) + "\n"

            if status == 'Failed':
                yield json.dumps({'status':'Failed... Retrying...'}) + "\n"

        if status != 'Failed':
            yield json.dumps({'status':status}) + "\n"
        else:
            yield json.dumps({'status':'Failed... will not retry...'}) + "\n"

    #check if camera can be reached
    response = connections.check_connectivity(constants['camera_ip'],4)
    if response['status'] == 'OK':
        return json.dumps({'status':response['message']}) + "\n"
    else: ##connect to camera
        return Response(connect_sequence(), mimetype='text/event-stream')

@app.route('/disconnect')
def disconnect():
    targetSSID = connections.getSSID(constants['camera_wifi_prefix'])
    connections.disconnect_wifi(targetSSID['message'])
    time.sleep(2)
    connectivity_result = connections.check_connectivity(constants['camera_ip'])
    if connectivity_result['status']=='error':
        status = {'status':'Camera disconnected'}
    else:
        status = {'status':'Failed: Camera still online'} 

    return json.dumps(status) + "\n"


@app.route('/parse')
def parse():
    mode = request.args.get('mode')

    ##get a list of the files that have already been downloaded 
    local_filelist = get_local_files(mode)

    html = requests.get('http://'+constants['camera_ip']+'/DCIM/'+mode+'/').text
    soup = BeautifulSoup(html, features="lxml")

    data = []
    table = soup.find('table')
    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]

        if len(cols) == 4:
            item_time = datetime.strptime(cols[2], "%Y/%m/%d %H:%M:%S").timestamp()

            if mode=='movie':
                file_extension = '.mp4'
            elif mode=='photo':
                file_extension = '.jpg'
            local_filename = str(int(item_time)) + file_extension

            if local_filename in local_filelist:
                link = cols[0]
                download_status = '<a href="/static/'+mode+'/'+local_filename+'">Downloaded</a>'
            else:
                download_status = '<a href="/download?file='+cols[0]+'&method=save&mode='+mode+'&date='+str(int(item_time))+'">Download</a>'
                link = '<a href="/download?file='+cols[0]+'&method=load&mode='+mode+'&date='+str(int(item_time))+'">'+cols[0]+'</a>'
            item = {
                'link':link,
                'size':cols[1],
                'date': cols[2],
                'status' : download_status 
            }
            data.append(item)

    return render_template('camera.html', records=data, colnames=['link','size','date','status'])

def get_local_files(mode):
    filelist = []
    for (dirpath, dirnames, filenames) in os.walk('static/'+mode+'/'):
        filelist.extend(filenames)
        break
    return filelist

@app.route('/download', methods=['GET'])
def download():
    mode = request.args.get('mode')
    method = request.args.get('method')

    #check if camera can be reached
    response = os.system(f"ping -c 1 {constants['camera_ip']}")

    if response != 0:
        return json.dumps({'status':'Camera Offline'} )   

    filename = request.args.get('file')
    url = 'http://'+constants['camera_ip']+'/DCIM/'+mode+'/'+filename

    import urllib.request

    response = urllib.request.urlopen(url)
    item = response.read()

    ##make the local filename the timestamp of the capture
    if mode=='movie':
        file_extension = '.mp4'
    elif mode=='photo':
        file_extension = '.jpg'
    
    if method == 'save':
        local_filename = str(request.args.get('date')) + file_extension
    elif method == 'load':
        local_filename = 'temp' + file_extension

    with open('static/'+mode+'/'+local_filename, "wb") as file:
        file.write(item)

    if mode == 'movie':
        render_string = '''
            <!doctype html>
            <html>
                <head>
                </head>
                <body>
                <video width="320" height="240" controls>
                    <source src="static'''+mode+'''"/"'''+local_filename+'''" type="video/mp4">
                </video>
                </body>
            </html>
            '''
    else:
        render_string = '''
            <!doctype html>
            <html>
                <head>
                </head>
                <body>
                <img width="100%" src="static/'''+mode+'''/'''+local_filename+'''" type="video/mp4">
                </body>
            </html>
            '''
    return render_template_string(render_string)

    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')