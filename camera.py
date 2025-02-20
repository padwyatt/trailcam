##functions for interacting with the camera
##delete

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import urllib.request
import random

def remote_list(camera_ip, mode):
    file_list = []

    try:
        html = requests.get('http://'+camera_ip+'/DCIM/'+mode+'/', timeout=3).text
        soup = BeautifulSoup(html, features="lxml")

        
        table = soup.find('table')
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]

            if len(cols) == 4:
                item_timestamp = datetime.strptime(cols[2], "%Y/%m/%d %H:%M:%S").timestamp()
                item = {
                    'name':cols[0],
                    'timestamp': int(item_timestamp),
                    'date': datetime.fromtimestamp(item_timestamp),
                    'link':None,
                    'type': mode,
                    'actions':['download','delete-remote']
                }

                file_list.append(item)
                status = 'OK'
    
    except Exception as e:
        status = 'error'    
    
    return {'status': status, 'file_list':file_list}

def get_local_files(mode):
    file_list = list(os.walk('static/'+mode+'/'))[0][2]
    local_files = []
    
    for local_file in file_list:
        item_timestamp = local_file.split('.')[0]
        if item_timestamp.isdigit():
            item_timestamp =  int(item_timestamp)
            item_date = datetime.fromtimestamp(int(item_timestamp))
        else:
            item_date = datetime.fromtimestamp(random.randrange(start=100))
            item_timestamp = random.randrange(start=100)

        local_files.append({
            'name': local_file,
            'timestamp': item_timestamp,
            'date': item_date,
            'link': 'static/'+mode+'/'+local_file,
            'type': mode,
            'actions': ['delete-local','view']
            }
        )

    return local_files

def copy_file(camera_ip, filename, filetype, filetime):
    try:
        url = 'http://'+camera_ip+'/DCIM/'+filetype+'/'+filename
        response = urllib.request.urlopen(url)
        item = response.read()

        ##make the local filename the timestamp of the capture
        if filetype=='movie':
            file_extension = '.mp4'
        elif filetype=='photo':
            file_extension = '.jpg'

        save_url = 'static/'+filetype+'/'+str(filetime) + file_extension

        with open(save_url, "wb") as file:
            file.write(item)
        
        return {'status':'OK','filelocation':save_url}
    
    except Exception as e:
        print(e)
        return {'status':'error','filelocation':None}
    
def delete_local(filename, filetype):
    try:
        local_url = 'static/'+filetype+'/'+filename
        os.remove(local_url)

        return {'status':'OK','message':'Local file deleted'}
    except Exception as e:
        print(e)
        return {'status':'error','message':'Could not delete local file'}    
    
def delete_remote(camera_ip,filename, filetype):
    url = 'http://'+camera_ip+'/DCIM/'+filetype+'/'+filename+'?del=1'
    return None