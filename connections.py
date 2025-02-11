import subprocess
from bluepy3.btle import UUID, Peripheral
import json
import time

def activate_wifi(camera_bluetooth_id,camera_bluetooth_service_id, camera_bluetooth_characteristic_id):
    #connect to bluetooth and activate the wifi
    try:
        p = Peripheral(camera_bluetooth_id, "random") #get the device
    except Exception as e:
        return {'status':'error', 'message': 'Cannot find bluetooth camera: ' + repr(e)}

    try:
        serv = p.getServiceByUUID(camera_bluetooth_service_id) #get service
    except Exception as e:
        #yield json.dumps({'status':'Cannot connect to relevant service: ' + repr(e)})  + "\n"
        return {'status':'error', 'message': 'Cannot connect to bluetooth camera: ' + repr(e)}
    
    try:
        c = serv.getCharacteristics(camera_bluetooth_characteristic_id)[0]
    except Exception as e:
        #yield {'status':'Cannot find relevant characteristic: ' + repr(e)}  + "\n"
        return {'status':'error', 'message': 'Cannot find relevant characteristic: ' + repr(e)}
    
    try:
        p.writeCharacteristic(c.valHandle+1,bytes("\x01\x00",encoding='utf-8')) 
        return {'status':'OK','message':'Wifi Turned On'}
    except Exception as e:
        #yield {'status':'Cannot write to relevant characteristic descriptor: ' + repr(e)}  + "\n"
        return {'status':'error', 'message': 'Cannot write to relevant characteristic descriptor: ' + repr(e)}
    
def getSSID(camera_wifi_prefix):
    ###Get the target SSID of the camera
    targetSSID = None
    t_end = time.time() + 20
    while (time.time() < t_end) & (targetSSID == None):
        proc = subprocess.run(['nmcli', '-t', '-f', 'SSID', 'dev', 'wifi'], stdout=subprocess.PIPE)
        if proc.returncode == 0:
            SSIDS = proc.stdout.decode('utf-8').strip().split('\n')
            print(SSIDS)
            for SSID in SSIDS:
                if camera_wifi_prefix in SSID:
                    targetSSID = SSID.strip()                
    if targetSSID == None:
        #yield json.dumps({'status':'Camera WiFi not found'})  + "\n"
        return {'status':'error', 'message': 'Camera Wifi not found'}
    else:
        return {'status':'OK', 'message': targetSSID}


def connect_wifi(targetSSID,camera_wifi_password):
    ####Attempt to connect to the WiFi
    t_end = time.time() + 20
    result = None
    while (time.time() < t_end) & (result != 0):
        proc = subprocess.run(["sudo","nmcli","d","wifi","connect",targetSSID,"password",camera_wifi_password],capture_output=True)
        result = proc.returncode
    if result == 0:
        return {'status':'OK', 'message':'WiFi connected...testing connection...'}
    else:
        return {'status':'error', 'message':'Wifi Failed to connect'}

def check_connectivity(camera_ip,timeout=10):
    ####Check connectivity
    t_end = time.time() + timeout
    result = None
    while (time.time() < t_end) & (result != 0):
        proc = subprocess.run(["ping","-c","1",camera_ip],capture_output=True)
        result = proc.returncode
    if result == 0:
        return {'status':'OK', 'message':'Camera Online!'}
    else:
        return {'status':'error', 'message':'Camera not Online'}

def disconnect_wifi(targetSSID):
    proc = subprocess.run(["sudo","nmcli","connection","delete",targetSSID],capture_output=True)
    result = proc.returncode
    if result == 0:
        return {'status':'OK', 'message':'Camera disconnected!'}
    else:
        return {'status':'error', 'message':'Camera count not disconnect'}

