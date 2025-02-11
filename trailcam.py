from bluepy3.btle import UUID, Peripheral

mac ='d6:39:32:33:7c:46' #bluetooth id of camera
p = Peripheral(mac, "random") #get the device
print(p)
serv = p.getServiceByUUID("0000ffe0-0000-1000-8000-00805f9b34fb") #get service
print(serv)
c = serv.getCharacteristics("0000ffeb-0000-1000-8000-00805f9b34fb")[0] #get cha>
print(c)
p.writeCharacteristic(c.valHandle+1,bytes("\x01\x00",encoding='utf-8')) #write >







