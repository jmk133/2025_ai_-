import pygame 
import time
from buildhat import *
from picamera2 import Picamera2
import cv2
import numpy as np
import time

# pygame.init()                                   #pygame initialize
# pygame.display.set_caption("Keyboard Control")  #window name
# screen = pygame.display.set_mode((200,200))     #window size
# screen.fill((0, 0, 0))                          #fill the screen with black

#set motors
lm = Motor('A')
rm = Motor('B')
lm.off()
rm.off()

def drive(speedl,speedr):
    lm.pwm(speedl*(-0.01))
    rm.pwm(speedr*(0.01))

def stop():
    rm.stop()
    lm.stop()

def motor_control(key):                        
    if key == 's':
        stop()
    if key == 'f':
        drive(15,10)
    if key == 'r':
        drive(15,0)
    if key == 'b':
        drive(-10,-10)
    if key == 'l':
        drive(0, 15)

def decision(x):
    if 60 < x <= 80:
        return 'f'
    elif x <= 60:
        return 'l'
    elif 80 <x:
        return 'r'
    else:
        return 'b'

def make_black(image, threshold=60): // threshold값 수정하여 올바르게 이미지 인식할 수 있도록 함
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    inverted_gray = cv2.bitwise_not(gray_image)
    black_image = cv2.inRange(inverted_gray, threshold, 255)
    return black_image, gray_image

def find_contour_center_and_draw(gray, original_image):
    crop_gray = gray[:, :]
    blur = cv2.GaussianBlur(crop_gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 123, 255, cv2.THRESH_BINARY_INV)

    mask = cv2.erode(thresh, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        c = max(contours, key=cv2.contourArea)  
        M = cv2.moments(c)
        if M['m00'] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])

            cv2.polylines(original_image, [c], isClosed=True, color=(0, 255, 0), thickness=2)


            print(f"Contour center: {cx}")
            return cx
        
    return None


picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (160), 120)})
picam2.configure(config)
picam2.start()

time.sleep(0.05)  
try:
    while True:

        frame = picam2.capture_array()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame_bgr_flipped = cv2.flip(frame_bgr, -1)
        black_image, gray = make_black(frame_bgr_flipped)
        cx = find_contour_center_and_draw(black_image, frame_bgr_flipped)
        if cx is not None:
            key = decision(cx)
            motor_control(key)
            print(f"Decision: {key}")
            time.sleep(0.1)
            

        cv2.imshow('Processed Frame', frame_bgr_flipped)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            motor_control("s")
            break
finally:
    picam2.stop()
    cv2.destroyAllWindows()
