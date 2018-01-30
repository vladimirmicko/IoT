import RPi.GPIO as GPIO
import imaplib 
import time 
import smtplib
import urllib 
import requests
import serial
import email
import httplib2
import json
import time
import datetime
from datetime import datetime

LEDred = 4
LEDgreen = 2 

GPIO.setmode(GPIO.BCM) 
GPIO.setwarnings(False) 

GPIO.setup(LEDred, GPIO.OUT) 
GPIO.setup(LEDgreen, GPIO.OUT) 

GPIO.output(LEDred, GPIO.LOW) 
GPIO.output(LEDgreen, GPIO.LOW) 

mail = imaplib.IMAP4_SSL('imap.gmail.com') 
mail.login("kravastrava@gmail.com", "kravastrava2014")
server = smtplib.SMTP('smtp.gmail.com', 587) 
server.starttls() 
server.login("kravastrava@gmail.com", "kravastrava2014") 

startTimeMailCheck = time.time()
startTimeMailSendTemp = time.time()
startTimeMailSendLight = time.time()
startTimeMailSendDist = time.time()
startTimeSerialCommunication = time.time()
startTimeCalculateAverageTemp = time.time()
startTimeCalculateAverageLight = time.time()
startTimeCalculateAverageDist = time.time()
startTimeConfigChanged = 0
startTimeObjectTooClose = 0
notificationFired=0

calculateAverageTempTime=200
calculateAverageLightTime=200
calculateAverageDistTime=200
configChangedTime=5
objectTooCloseTime=5

tempCall="period"
lightCall="period"
distCall="period"

writeKey = 'QEO7G66O96GRNHSQ'
readKey = '5FNMUFIG335XC136'

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=0)

temp=[]
light=[]
dist=[]
aTemp=0
aLight=0
aDist=0

def sendNotification():
	global notificationFired, objectTooCloseTime
	if(time.time()-notificationFired >= objectTooCloseTime):
		notificationFired=time.time()
	    	httplib2.debuglevel     = 0
	    	http                    = httplib2.Http()
	    	content_type_header     = "application/json"
	    	url = "https://maker.ifttt.com/trigger/ObjectTooClose/with/key/gQE9C_coVl5xSzbcNVA2zloldnPSo-6OIHp8CPMlurA"
		headers = {'Content-Type': content_type_header}
	 	response, content = http.request( url,'GET', headers=headers)
	        #print (response)
	        print (content)

def sendMailTemp():
	report="Prosecna temperatura u poslednjih "+str(calculateAverageTempTime)+" sekundi je "+str(aTemp)+" Celzijusa\n"
	msg = 'Subject: {}\n\n{}'.format("Temperatura ", report) 
	server.sendmail("kravastrava@gmail.com", "vladimirmicko@gmail.com", msg) 
	print("Temp mail sent")

def sendMailLight():
	report="Prosecna osvetljenost u poslednjih "+str(calculateAverageLightTime)+" sekundi je "+str(aLight)+" luxa\n"
	msg = 'Subject: {}\n\n{}'.format("Osvetljenost ", report) 
	server.sendmail("kravastrava@gmail.com", "vladimirmicko@gmail.com", msg) 
	print("Light mail sent")

def sendMailDist():
	report="Prosecna razdaljina u poslednjih "+str(calculateAverageDistTime)+" sekundi je "+str(aDist)+" centimetara\n"
	msg = 'Subject: {}\n\n{}'.format("Razdaljina ", report) 
	server.sendmail("kravastrava@gmail.com", "vladimirmicko@gmail.com", msg) 
	print("Dist mail sent")

def markMailsSeen(array):
	for num in array: 
		mail.store(num,'+FLAGS','\\Seen')

def extractMailBody(data):
	body=""
	for responsePart in data:
		if isinstance(responsePart, tuple):
			msg=email.message_from_string(responsePart[1])
			for part in msg.walk():
				if part.get_content_type()=="text/plain":
					body=part.get_payload(decode=True)
	return body

def checkMail():
	global tempCall, lightCall, distCall
	global calculateAverageTempTime,calculateAverageLightTime,calculateAverageDistTime
	global startTimeConfigChanged

	mail.select("inbox")  
	retcode1, response1 = mail.search(None, '(SUBJECT "Posalji" UNSEEN)') 
	retcode2, response2 = mail.search(None, '(SUBJECT "K" UNSEEN)') 

	if (len(response1[0].split()) > 0 ):
		mailIdList=response1[0].split()
		for m in mailIdList:
			type, data = mail.fetch(m,'(RFC822)')
			body=extractMailBody(data)
			bodyLines=body.splitlines()
			print("Body Posalji")
			print(body)
			if(tempCall=="zahtev" and bodyLines[0]=="Temperatura"):
				sendMailTemp()
			elif(lightCall=="zahtev" and bodyLines[0]=="Osvetljenost"):
				sendMailLight()
			elif(distCall=="zahtev" and bodyLines[0]=="Razdaljina"):
				sendMailDist()
	elif (len(response2[0].split()) > 0 ):
		mailIdList=response2[0].split()
		for m in mailIdList:
			type, data = mail.fetch(m,'(RFC822)')
			body=extractMailBody(data)
			print("Body Konfiguracija")
			print(body)
			bodyLines=body.splitlines()
			for line in bodyLines:
				if(line.split(':')[0]=="Temperatura"):
					if(line.split(':')[1].split(',')[0]=="zahtev"):
						tempCall="zahtev"
					else:
						tempCall="period"
					calculateAverageTempTime=int(line.split(':')[1].split(',')[1])

				if(line.split(':')[0]=="Osvetljenost"):
					if(line.split(':')[1].split(',')[0]=="zahtev"):
						lightCall="zahtev"
					else:
						lightCall="period"
					calculateAverageLightTime=int(line.split(':')[1].split(',')[1])

				if(line.split(':')[0]=="Razdaljina"):
					if(line.split(':')[1].split(',')[0]=="zahtev"):
						distCall="zahtev"
					else:
						distCall="period"
					calculateAverageDistTime=int(line.split(':')[1].split(',')[1])

			startTimeConfigChanged=time.time()
			print("Konfiguracija")
			print(tempCall,lightCall,distCall)
			print(calculateAverageTempTime,calculateAverageLightTime,calculateAverageDistTime)



def convertTemp(x):
	y=x*0.28
	return y

def convertLight(x):
	if(x>=0 and x<=20):
		y=x/200
	elif(x>20 and x<=122):
		y=(x/113.3)-0.07
	elif(x>122 and x<=520):
		y=(x/44.2)-1.7
	elif(x>520 and x<=881):
		y=(x/4.01)-119.7
	elif(x>881 and x<=1024):
		y=(x/0.15)-5826
	else:
		y=0
	y=round(y,2)
	return y

def convertDist(x):
	global startTimeObjectTooClose
	if(x<5):
		startTimeObjectTooClose=time.time()
		sendNotification()
	return x

def serialRead():
	message=ser.readline() 
	while(message != ""):
		values=message.split(" ")
		if(len(values)==4):
			try:
				temp.append(convertTemp(int(values[0])))
				light.append(convertLight(int(values[1])))
				dist.append(convertDist(int(values[2])))
				#print("Received message: "+message)
				#print("temp: "+str(convertTemp(int(values[0])))+"C     light: "+str(convertLight(int(values[1])))+"lux     dist: "+str(convertDist(int(values[2])))+"cm")
			except ValueError:
				pass
		message=ser.readline() 

def calculateAverageTemp():
	global temp, aTemp
	aTemp=0
	for x in temp:
		aTemp=aTemp+float(x)

	aTemp=round(aTemp/len(temp),2)
	print("Temp: "+str(aTemp))
	temp=[]

def calculateAverageLight():
	global light, aLight
	aLight=0
	for x in light:
		aLight=aLight+float(x)

	aLight=round(aLight/len(light),2)
	print("Light: "+str(aLight))
	temp=[]

def calculateAverageDist():
	global dist, aDist
	aDist=0
	for x in dist:
		aDist=aDist+float(x)

	aDist=round(aDist/len(dist),2)
	print("Dist: "+str(aDist))
	dist=[]



while True: 
	if(time.time()-startTimeMailCheck >= 10):
		startTimeMailCheck=time.time()
		checkMail()
		print("Mail checked")
	
	if(time.time()-startTimeSerialCommunication >= 1):
		startTimeSerialCommunication=time.time()
		serialRead()

	if(time.time()-startTimeCalculateAverageTemp >= calculateAverageTempTime):
		startTimeCalculateAverageTemp=time.time()
		calculateAverageTemp()
		if(tempCall=="period"):
			sendMailTemp()	

	if(time.time()-startTimeCalculateAverageLight >= calculateAverageLightTime):
		startTimeCalculateAverageLight=time.time()
		calculateAverageLight()
		if(lightCall=="period"):
			sendMailLight()

	if(time.time()-startTimeCalculateAverageDist >= calculateAverageDistTime):
		startTimeCalculateAverageDist=time.time()
		calculateAverageDist()
		if(distCall=="period"):
			sendMailDist()

	if(time.time()-startTimeConfigChanged >= configChangedTime):
		GPIO.output(LEDgreen, GPIO.LOW)
	else: 
		GPIO.output(LEDgreen, GPIO.HIGH)

	if(time.time()-startTimeObjectTooClose >= objectTooCloseTime):
		GPIO.output(LEDred, GPIO.LOW)
	else:
		GPIO.output(LEDred, GPIO.HIGH)
