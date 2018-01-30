import RPi.GPIO as GPIO
import imaplib 
import time 
import smtplib
import urllib 
import requests
from datetime import datetime


LEDred = 4
LEDgreen = 2 
SENSOR = 3

GPIO.setmode(GPIO.BCM) 
GPIO.setwarnings(False) 

GPIO.setup(LEDred, GPIO.OUT) 
GPIO.setup(LEDgreen, GPIO.OUT) 
GPIO.setup(SENSOR, GPIO.IN) 

GPIO.output(LEDred, GPIO.LOW) 
GPIO.output(LEDgreen, GPIO.LOW) 

mail = imaplib.IMAP4_SSL('imap.gmail.com') 
mail.login("kravastrava@gmail.com", "kravastrava2014")

startTimeMailCheck = time.time()
startTimeMailSend = time.time()
startTimeThingspeak = time.time()

sensorState=GPIO.input(SENSOR) 
sensorChange=0

writeKey = 'QEO7G66O96GRNHSQ'
readKey = '5FNMUFIG335XC136'

def markMailsSeen(array):
	for num in array: 
		mail.store(num,'+FLAGS','\\Seen')

def checkMail():
	mail.select("inbox") # connect to inbox. 
	retcode1, response1 = mail.search(None, '(SUBJECT "Ron" UNSEEN)') 
	retcode2, response2 = mail.search(None, '(SUBJECT "Roff" UNSEEN)') 
	retcode3, response3 = mail.search(None, '(SUBJECT "Gon" UNSEEN)') 
	retcode4, response4 = mail.search(None, '(SUBJECT "Goff" UNSEEN)') 

	if (len(response1[0].split()) > 0 ) :
		GPIO.output(LEDred, GPIO.HIGH) 
		markMailsSeen(response1[0].split())
		print("Crvena dioda Upaljena") 
	elif (len(response2[0].split()) > 0 ) : 
		GPIO.output(LEDred, GPIO.LOW) 
		markMailsSeen(response2[0].split())
		print("Crvena dioda ugasena") 
	elif (len(response3[0].split()) > 0 ) : 
		GPIO.output(LEDgreen, GPIO.HIGH) 
		markMailsSeen(response3[0].split())
		print("Zelena dioda upaljena") 
	elif (len(response4[0].split()) > 0 ) : 
		GPIO.output(LEDgreen, GPIO.LOW) 
		markMailsSeen(response4[0].split())
		print("Zelena dioda ugasena") 


def sensorCheck():
	global sensorState
	global sensorChange
	if (sensorState!=GPIO.input(SENSOR)):
		sensorState=GPIO.input(SENSOR)
		sensorChange=sensorChange+1
		print("Senzor pomeraja - PROMENA - "+str(sensorChange))

def sendMail():
	report="Zelena dioda: "+("upaljena" if GPIO.input(LEDgreen)==1 else "ugasena")+"\n"
	report=report+"Crvena dioda: "+("upaljena" if GPIO.input(LEDred)==1 else "ugasena")+"\n"
	report=report+"Ukupan broj pomeraja: "+str(sensorChange)


	server = smtplib.SMTP('smtp.gmail.com', 587) 
	server.starttls() 
	server.login("kravastrava@gmail.com", "kravastrava2014") 
	msg = 'Subject: {}\n\n{}'.format("Izvestaj "+datetime.now().strftime('%H:%M'), report) 
	server.sendmail("kravastrava@gmail.com", "vladimirmicko@gmail.com", msg) 
	server.quit() 

def thingspeak():
	params = {'field1': sensorChange, 'api_key':writeKey }
	headers = {"Content-typZZe": "application/x-www-form-urlencoded","Accept": "text/plain"} 
	r=requests.post("https://api.thingspeak.com/update", params, headers)



while True: 
	sensorCheck()

	if(time.time()-startTimeMailCheck >= 10):
		startTimeMailCheck=time.time()
		checkMail()
		print("Mail checked")
	
	if(time.time()-startTimeMailSend >= 60):
		startTimeMailSend=time.time()
		sendMail()
		print("Mail sent")

	if(time.time()-startTimeThingspeak >= 60):
		startTimeThingspeak=time.time()
		thingspeak()
		sensorChange=0
		print("Thingspeak data sent")






