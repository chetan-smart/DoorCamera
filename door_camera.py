
import atexit
import io
import os
import os.path
import picamera
import pygame
import time
import yuv2rgb
import subprocess
from subprocess import call  
from pygame.locals import *
import RPi.GPIO as GPIO
import datetime

os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV'      , '/dev/fb1')
os.putenv('SDL_MOUSEDRV'   , 'TSLIB')
os.putenv('SDL_MOUSEDEV'   , '/dev/input/touchscreen')

# Buffers for viewfinder data
rgb = bytearray(320 * 240 * 3)
yuv = bytearray(320 * 240 * 3 / 2)

pygame.init()
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)

camera            = picamera.PiCamera()
atexit.register(camera.close)
camera.awb_mode   = 'incandescent';
camera.crop       = (0.0, 0.0, 1.0, 1.0)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.IN)         #Read output from PIR motion sensor

os.environ['DISPLAY'] = ":0"

timeLastPictureTaken = time.time()
timeLastTouch = time.time()

screenTouch = False

while(True):

  for event in pygame.event.get():
    if(event.type is MOUSEBUTTONDOWN):
      screenTouch = True
      timeLastTouch = time.time()

  motionDetected = GPIO.input(21)

  if motionDetected == 0 and screenTouch == False: 
    subprocess.call('xset dpms force off', shell=True)
    screen.fill((0,0,0))

  if motionDetected == 1 or screenTouch == True:
    subprocess.call('xset dpms force on', shell=True)
    
    stream = io.BytesIO() # Capture into in-memory stream
    camera.resolution = (320,240)
    camera.capture(stream, use_video_port=True, format='raw')

    if time.time() - timeLastPictureTaken > 10:
        now = str(datetime.datetime.now())
        now = now.replace(" ", "_")
        filename = '/home/pi/Pictures/' + now + '.JPG';
        camera.resolution = (2592, 1944)
        camera.capture(filename, use_video_port=False, format='jpeg', thumbnail=None)
        timeLastPictureTaken = time.time()

    if time.time() - timeLastTouch > 30:
        screenTouch = False
        timeLastTouch = time.time()

    stream.seek(0)
    stream.readinto(yuv)  # stream -> YUV buffer
    stream.close()
    yuv2rgb.convert(yuv, rgb, 320,240)

    img = pygame.image.frombuffer(rgb[0:320 * 240 * 3],(320,240), 'RGB')

    screen.blit(img, ((320 - img.get_width() ) / 2, (240 - img.get_height()) / 2))

  pygame.display.update()
