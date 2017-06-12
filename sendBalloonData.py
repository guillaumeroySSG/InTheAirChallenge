#! /usr/bin/python
# Written by Dan Mandle http://dan.mandle.me September 2012
# License: GPL 2.0

import os
from gps import *
from time import *
import time
import threading
import subprocess
import os
import glob
import time
import sys
import RPi.GPIO as GPIO

gpsd = None #seting the global variable

GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT, initial=GPIO.HIGH)

#pour activer le module de temperature
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

def read_temp_raw():
 f = open(device_file, 'r')
 lines = f.readlines()
 f.close()
 return lines
 
def read_temp():
 lines = read_temp_raw()
 while lines[0].strip()[-3:] != 'YES':
  time.sleep(0.2)
 lines = read_temp_raw()
 equals_pos = lines[1].find('t=')
 if equals_pos != -1:
  temp_string = lines[1][equals_pos+2:]
  temp_c = float(temp_string) / 1000.0
  temp_f = temp_c * 9.0 / 5.0 + 32.0
 return temp_c, temp_f

def format_hex(value):
   # on enleve les 0x
   strRes = str(value)[2:]
   # on complete avec des 0 pour avoir 1 hexa sur 4 bit
   i = 0
   longueurChaine = len(strRes)
   while i < (4 - longueurChaine):
    strRes = '0' + strRes
    i=i+1
   return strRes

os.system('clear') #clear the terminal (optional)

class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd #bring it in scope
    gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
    self.current_value = None
    self.running = True #setting the thread running to true

  def run(self):
    global gpsd
    while gpsp.running:
      gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer

if __name__ == '__main__':
  gpsp = GpsPoller() # create the thread
  try:
    gpsp.start() # start it up
    while True:
      #It may take a second or two to get good data
      #print gpsd.fix.latitude,', ',gpsd.fix.longitude,'  Time: ',gpsd.utc
      cmdSigfox   = 'sudo python /home/pi/rpisigfox/sendsigfox.py '
      os.system('clear')
      print
      print ' GPS reading'
      print '----------------------------------------'
      print 'latitude    ' , gpsd.fix.latitude
      gpsLat = gpsd.fix.latitude
      print 'longitude   ' , gpsd.fix.longitude
      gpsLong = gpsd.fix.longitude
      print 'time utc    ' , gpsd.utc,' + ', gpsd.fix.time
      os.system('sudo raspistill -o /home/pi/InTheAirChallenge/img_sonde_'+time.strftime("%H:%M:%S")+'.jpg -w 640 -h 480')
      print 'altitude (m)' , gpsd.fix.altitude
      gpsAlt = gpsd.fix.altitude
      print 'eps         ' , gpsd.fix.eps
      print 'epx         ' , gpsd.fix.epx
      print 'epv         ' , gpsd.fix.epv
      print 'ept         ' , gpsd.fix.ept
      print 'speed (m/s) ' , gpsd.fix.speed
      print 'climb       ' , gpsd.fix.climb
      print 'track       ' , gpsd.fix.track
      print 'mode        ' , gpsd.fix.mode
      print 'sats        ' , gpsd.satellites
      print 'temp        ' , read_temp()[0]

      #construction de la trame pour la longitude avec decalage pour ne pas avoir a traiter une longitude negative
      if str(gpsLong) in 'nan':
         cmdSigfox = cmdSigfox + '000000'
      else :
         cmdSigfox = cmdSigfox + format_hex(hex(int(str(gpsLong).split('.',1)[0])+5)) + format_hex(hex(int(str(gpsLong).split('.',1)[1][:4])))

      # construction de la trame pour la latitude
      if str(gpsLat) in 'nan':      
          cmdSigfox = cmdSigfox + '000000'
      else :
          cmdSigfox = cmdSigfox + format_hex(hex(int(str(gpsLat).split('.',1)[0]))) + format_hex(hex(int(str(gpsLat).split('.',1)[1][:4])))
      
      # construction de la trame pour l'altitude
      if str(gpsAlt) in 'nan':
         cmdSigfox = cmdSigfox + '00'
      else :
         cmdSigfox = cmdSigfox + format_hex(hex(int(str(gpsAlt).split('.',1)[0])))
      # construction de la trame pour la temperature. Ajout de 50 pour ne pas gerer les temperature negative
      if str(read_temp()[0]) in 'nan':
         cmdSigfox = cmdSigfox + '00'
      else :
         cmdSigfox = cmdSigfox + format_hex(hex(int(str(read_temp()[0]+50).split('.',1)[0])))

      print cmdSigfox
      os.system(cmdSigfox)
      time.sleep(300) #set to whatever

  except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
    print "\nKilling Thread..."
    gpsp.running = False
    gpsp.join() # wait for the thread to finish what it's doing
    print "Done.\nExiting."
