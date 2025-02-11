import os

command = """sudo iwlist wlan0 scan | grep -o -P '(?<=ESSID:").*(?=")'"""
result = os.popen(command)
SSIDS = list(result)

targetSSID = None

for SSID in SSIDS:
   if "4K WIFI CAM-" in SSID:
      targetSSID = SSID.strip()
      try:
         os.system("sudo nmcli d wifi connect '{}' password '{}'".format(targetSSID,'12345678'))
      except:
         raise
      else:
         print("connected")

if targetSSID == None:
   print("Camera not found")


