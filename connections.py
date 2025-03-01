import subprocess
from bluepy3.btle import UUID, Peripheral
import json
import time
import shared

def activate_wifi(camera_bluetooth_id,camera_bluetooth_service_id, camera_bluetooth_characteristic_id):
    #connect to bluetooth and activate the wifi
    try:
        p = Peripheral(camera_bluetooth_id, "random") #get the device
    except Exception as e:
        message = {'status':'error', 'message': 'Cannot find bluetooth camera: ' + repr(e)}
        shared.log_message(message['message'])
        return message
    try:
        serv = p.getServiceByUUID(camera_bluetooth_service_id) #get service
    except Exception as e:
        message = {'status':'error', 'message': 'Cannot connect to bluetooth camera: ' + repr(e)}
        shared.log_message(message['message'])
        return message

    try:
        c = serv.getCharacteristics(camera_bluetooth_characteristic_id)[0]
    except Exception as e:
        message = {'status':'error', 'message': 'Cannot find relevant characteristic: ' + repr(e)}
        shared.log_message(message['message'])
        return message
    
    try:
        p.writeCharacteristic(c.valHandle+1,bytes("\x01\x00",encoding='utf-8')) 
        p.disconnect()
        message = {'status':'OK','message':'Wifi Turning on...'}
        shared.log_message(message['message'])
        return message
    except Exception as e:
        p.disconnect()
        message =  {'status':'error', 'message': 'Cannot write to relevant characteristic descriptor: ' + repr(e)}
        shared.log_message(message['message'])
        return message


def getSSID(camera_wifi_prefix,timeout=20):
    ###Get the target SSID of the camera
    targetSSID = None
    t_end = time.time() + timeout
    while (time.time() < t_end) & (targetSSID == None):
        proc = subprocess.run(['nmcli', '-t', '-f', 'SSID', 'dev', 'wifi'], stdout=subprocess.PIPE)
        if proc.returncode == 0:
            SSIDS = proc.stdout.decode('utf-8').strip().split('\n')
            print(SSIDS)
            for SSID in SSIDS:
                if camera_wifi_prefix in SSID:
                    targetSSID = SSID.strip()                
    if targetSSID == None:
        message = {'status':'error', 'message': 'Camera Wifi not found','targetSSID':None}
        shared.log_message(message['message'] + ' - Found:'+','.join(SSIDS))
        return message
    else:
        message = {'status':'OK', 'message':'Wifi '+targetSSID+' activated','targetSSID': targetSSID}
        shared.log_message(message['message'])
        return message


def connect_wifi(targetSSID,camera_wifi_password):
    ####Attempt to connect to the WiFi
    t_end = time.time() + 20
    result = None
    while (time.time() < t_end) & (result != 0):
        proc = subprocess.run(["sudo","nmcli","d","wifi","connect",targetSSID,"password",camera_wifi_password],capture_output=True)
        result = proc.returncode
    if result == 0:
        message =  {'status':'OK', 'message':'WiFi connected...testing connection...'}
        shared.log_message(message['message'])
        return message
    else:
        message = {'status':'error', 'message':'Wifi Failed to connect'}
        shared.log_message(message['message'])
        return message

def check_connectivity(camera_ip,timeout=10):
    ####Check connectivity
    t_end = time.time() + timeout
    result = None
    while (time.time() < t_end) & (result != 0):
        proc = subprocess.run(["ping","-c","1",camera_ip],capture_output=True)
        result = proc.returncode
    if result == 0:
        message = {'status':'OK', 'message':'Camera Online!'}
        shared.log_message(message['message'])
        return message
    else:
        message = {'status':'error', 'message':'Camera not Online'}
        shared.log_message(message['message'])
        return message

def disconnect_wifi(targetSSID, camera_ip):
    proc = subprocess.run(["sudo","nmcli","connection","delete",targetSSID],capture_output=True)
    result = proc.returncode
    if result == 0:
        time.sleep(5)
        connectivity_result = check_connectivity(camera_ip)
        if connectivity_result['status']=='error':
            message =  {'status':'OK', 'message':'Camera disconnected!'}
            shared.log_message(message['message'])
            return message
        else:
            message = {'status':'error', 'message':'Camera could not disconnect'}
            shared.log_message(message['message'])
            return message
    else:
        message = {'status':'error', 'message':'Camera could not disconnect'}
        shared.log_message(message['message'])
        return message

def connect_sequence(camera_ip, camera_wifi_prefix,camera_wifi_password, camera_bluetooth_id,camera_bluetooth_service_id,camera_bluetooth_characteristic_id):
    status = None
    max_retries = 3
    loop = 0

    while (loop < max_retries) & (status != 'OK'):
        loop += 1
        message = {'status':'None','message':'Activating WiFi (attempt '+str(loop)+'/3)'}
        shared.log_message(message['message'])
        yield json.dumps(message) + "\n"

        ##check if the network is already broadcasting
        getSSID_result = getSSID(camera_wifi_prefix,10)

        ##if it is not broadcasting, attempt to activate it
        if getSSID_result['status'] == 'error':
            bluetooth_result = activate_wifi(camera_bluetooth_id,camera_bluetooth_service_id,camera_bluetooth_characteristic_id)
            if bluetooth_result['status'] == 'OK':
                yield json.dumps(bluetooth_result) + "\n" 
                getSSID_result = getSSID(camera_wifi_prefix,20)
            else:
                yield json.dumps(bluetooth_result) + "\n"
        else:
            yield json.dumps(getSSID_result) + "\n" 

        ##if the network is broadcasting, attempt to connect to it
        if getSSID_result['status'] == 'OK':
            activation_result = connect_wifi(getSSID_result['targetSSID'], camera_wifi_password)
            yield json.dumps(activation_result) + "\n"
        else:
            activation_result = {'status':'error'}
            yield json.dumps(getSSID_result) + "\n"
            time.sleep(2)

        #If wifi is activated correctly, check connectivity
        if activation_result['status'] == 'OK':
            connectivity_result = check_connectivity(camera_ip)
            status=connectivity_result['status']

        if status == 'Failed':
            message = {'status':'error','message':'Failed... Retrying...'}
            shared.log_message(message['message'])
            yield json.dumps(message) + "\n"

    if status == 'OK':
        yield json.dumps(connectivity_result) + "\n" 
    else:
        message = {'status':'error','message':'Failed... will not retry...'}
        shared.log_message(message['message'])
        yield json.dumps(message) + "\n"
