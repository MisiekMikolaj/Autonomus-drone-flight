import cv2
import numpy as np
import datetime
import time
from djitellopy import Tello


from djitellopy import Tello
import cv2
from djitellopy import tello
from threading import Thread, Event
import keyboard
import os
import time
import csv
from simple_pid import PID
import cv2
import numpy as np
import math
import matplotlib.pyplot as plt

krok=0
frameWidth = 640
frameHeight = 480
cap = cv2.VideoCapture(0)
cap.set(3, frameWidth)
cap.set(4, frameHeight)

deadZone=100



startCounter =0

# CONNECT TO TELLO
me = tello.Tello()
me.connect()

print(me.get_battery())
# me.for_back_velocity = 0
# me.left_right_velocity = 0
# me.up_down_velocity = 0
# me.yaw_velocity = 0
# me.speed = 0

#me.streamoff()
me.streamon()

global imgContour

def empty(a):
    pass

cv2.namedWindow("HSV")
cv2.resizeWindow("HSV",640,240)
cv2.createTrackbar("HUE Min","HSV",19,179,empty)
cv2.createTrackbar("HUE Max","HSV",35,179,empty)
cv2.createTrackbar("SAT Min","HSV",107,255,empty)
cv2.createTrackbar("SAT Max","HSV",255,255,empty)
cv2.createTrackbar("VALUE Min","HSV",89,255,empty)
cv2.createTrackbar("VALUE Max","HSV",255,255,empty)

cv2.namedWindow("Parameters")
cv2.resizeWindow("Parameters",640,240)
cv2.createTrackbar("Threshold1","Parameters",166,255,empty)
cv2.createTrackbar("Threshold2","Parameters",171,255,empty)
cv2.createTrackbar("Area","Parameters",1500,30000,empty)


def stackImages(scale,imgArray):
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]
    if rowsAvailable:
        for x in range ( 0, rows):
            for y in range(0, cols):
                if imgArray[x][y].shape[:2] == imgArray[0][0].shape [:2]:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (0, 0), None, scale, scale)
                else:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (imgArray[0][0].shape[1], imgArray[0][0].shape[0]), None, scale, scale)
                if len(imgArray[x][y].shape) == 2: imgArray[x][y]= cv2.cvtColor( imgArray[x][y], cv2.COLOR_GRAY2BGR)
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank]*rows
        hor_con = [imageBlank]*rows
        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            if imgArray[x].shape[:2] == imgArray[0].shape[:2]:
                imgArray[x] = cv2.resize(imgArray[x], (0, 0), None, scale, scale)
            else:
                imgArray[x] = cv2.resize(imgArray[x], (imgArray[0].shape[1], imgArray[0].shape[0]), None,scale, scale)
            if len(imgArray[x].shape) == 2: imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
        hor= np.hstack(imgArray)
        ver = hor
    return ver

def getContours(img,imgContour):
    global dir
    contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        areaMin = cv2.getTrackbarPos("Area", "Parameters")
        if area > areaMin:
            cv2.drawContours(imgContour, cnt, -1, (255, 0, 255), 7)
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            x , y , w, h = cv2.boundingRect(approx)
            cv2.rectangle(imgContour, (x , y ), (x + w , y + h ), (0, 255, 0), 5)
            cv2.putText(imgContour, "Points: " + str(len(approx)), (x + w + 20, y + 20), cv2.FONT_HERSHEY_COMPLEX, .7,(0, 255, 0), 2)
            cv2.putText(imgContour, "Area: " + str(int(area)), (x + w + 20, y + 45), cv2.FONT_HERSHEY_COMPLEX, 0.7,(0, 255, 0), 2)
            cv2.putText(imgContour, " " + str(int(x))+ " "+str(int(y)), (x - 20, y- 45), cv2.FONT_HERSHEY_COMPLEX, 0.7,(0, 255, 0), 2)

            cx = int(x + (w / 2))
            cy = int(y + (h / 2))

            if (cx <int(frameWidth/2)-deadZone):
                cv2.putText(imgContour, " GO LEFT " , (20, 50), cv2.FONT_HERSHEY_COMPLEX,1,(0, 0, 255), 3)
                dir = 1
            elif (cx > int(frameWidth / 2) + deadZone):
                cv2.putText(imgContour, " GO RIGHT ", (20, 50), cv2.FONT_HERSHEY_COMPLEX,1,(0, 0, 255), 3)
                dir = 2
            elif (cy < int(frameHeight / 2) - deadZone):
                cv2.putText(imgContour, " GO UP ", (20, 50), cv2.FONT_HERSHEY_COMPLEX,1,(0, 0, 255), 3)
                dir = 3
            elif (cy > int(frameHeight / 2) + deadZone):
                cv2.putText(imgContour, " GO DOWN ", (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1,(0, 0, 255), 3)
                dir = 4
            else: dir = 0

            cv2.line(imgContour, (int(frameWidth/2),int(frameHeight/2)), (cx,cy),(0, 0, 255), 3)

def display(img):
    cv2.line(img,(int(frameWidth/2)-deadZone,0),(int(frameWidth/2)-deadZone,frameHeight),(255,255,0),3)
    cv2.line(img,(int(frameWidth/2)+deadZone,0),(int(frameWidth/2)+deadZone,frameHeight),(255,255,0),3)

    cv2.circle(img,(int(frameWidth/2),int(frameHeight/2)),5,(0,0,255),5)
    cv2.line(img, (0,int(frameHeight / 2) - deadZone), (frameWidth,int(frameHeight / 2) - deadZone), (255, 255, 0), 3)
    cv2.line(img, (0, int(frameHeight / 2) + deadZone), (frameWidth, int(frameHeight / 2) + deadZone), (255, 255, 0), 3)

def calculate_area(contour, mask):
    contours_mask = np.zeros_like(mask)
    cv2.drawContours(contours_mask, [contour], 0, 255, -1)

    return np.count_nonzero(mask[contours_mask == 255])

lower = np.array([0,0,0])
upper = np.array([0,0,0])
zn_z = False
zn_c = False
is_color_detected = False
stop_szukanie = False
zatrzymany = False
timer = datetime.datetime.now()
krok = 0

while True:

    img = me.get_frame_read().frame
    img = cv2.resize(img, (frameWidth, frameHeight))


    imgContour = img.copy()
    imgHsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)

    h_min = cv2.getTrackbarPos("HUE Min","HSV")
    h_max = cv2.getTrackbarPos("HUE Max", "HSV")
    s_min = cv2.getTrackbarPos("SAT Min", "HSV")
    s_max = cv2.getTrackbarPos("SAT Max", "HSV")
    v_min = cv2.getTrackbarPos("VALUE Min", "HSV")
    v_max = cv2.getTrackbarPos("VALUE Max", "HSV")

    zielony = cv2.inRange(imgHsv,(38, 106, 67),(179, 255, 147))
    czerwony = cv2.inRange(imgHsv, (0,131,39), (89,255,255))

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    zielony = cv2.morphologyEx(zielony, cv2.MORPH_CLOSE, kernel, iterations=3)
    czerwony = cv2.morphologyEx(czerwony, cv2.MORPH_CLOSE, kernel, iterations=3)

    contours_z, _ = cv2.findContours(zielony, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours_c, _ = cv2.findContours(czerwony, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    ################# FLIGHT
    if startCounter == 0:
        #me.takeoff()
        time.sleep(1)
        me.streamon()
        startCounter = 1
    if len(contours_z) < 6500  and len(contours_c) < 6500 and is_color_detected == False and krok == 0:
        print("obroc sie")
        #me.yaw_velocity = -60
        me.send_rc_control(0, 0, 0, -30)
        krok = 1
    elif is_color_detected == True  and dir == 0 and  krok == 1:
        print('************************stop*********************')
        #me.yaw_velocity = 0
        me.send_rc_control(0, 0, 0, 0)
        krok = 2
    elif is_color_detected == True  and (krok == 2 or krok == 0):
        print('zatrzymany')
        krok = 3
    elif krok == 3:
        print('lec w lewo')
        me.send_rc_control(-30,0,0,0)
        time.sleep(3)
        timer = datetime.datetime.now()
        krok = 4
    elif len(contours_z) < 500  and len(contours_c) < 500 and krok == 4:
        print('brak')
        me.send_rc_control(0, 0, 0, 0)
        is_color_detected = False
        krok = 5
    elif timer + datetime.timedelta(0,4) < datetime.datetime.now()  and krok == 5:
        print('lec w prawo')
        me.send_rc_control(30, 0, 0, 0)
        krok = 6
    elif is_color_detected == True  and dir == 0 and krok == 5:
        print('Wykryto drugie po lewej')
        me.send_rc_control(0, 0, 0, 0)
        time.sleep(0.5)
        krok = 7
    elif is_color_detected == True and dir == 0 and krok == 6:
        print('lec w prawo daaaaaleeeejjjj')
        me.send_rc_control(0, 0, 0, 0)
        time.sleep(3)
        me.send_rc_control(30, 0, 0, 0)
        time.sleep(1)
        krok = 8
    elif len(contours_z) < 500  and len(contours_c) < 500 and krok == 8:
        is_color_detected = False
        krok = 9
    elif is_color_detected == True and dir == 0 and krok == 9:
        print('Wykryto drugie po prawej')
        me.send_rc_control(0, 0, 0, 0)
        time.sleep(1)
        krok = 10
    elif krok == 7:
        print('lec w prawo o poł odległosic')
        if zn_z == True:
            me.send_rc_control(30, 0, 0, 0)
            time.sleep(1.5) # czas przelotu
            print('stop')
            me.send_rc_control(0, 0, 0, 0)
            krok = 11
        elif zn_c == True:
            me.send_rc_control(30, 0, 0, 0)
            time.sleep(1.5)
            print('stop')
            me.send_rc_control(0, 0, 0, 0)
            krok = 11

    elif krok == 10:
        print('lec w lewo o poł odległosic')
        if zn_z == True:
            me.send_rc_control(-30, 0, 0, 0)
            time.sleep(1.5)
            print('stop')
            me.send_rc_control(0, 0, 0, 0)
            krok = 11
        elif zn_c == True:
            me.send_rc_control(-30, 0, 0, 0)
            time.sleep(1.5)
            print('stop')
            me.send_rc_control(0, 0, 0, 0)
            krok = 11

    elif krok == 11:
        print('lec do przodu')
        me.send_rc_control(0, 30, 0, 0)
        time.sleep(4)
        print('stop - koniec')
        me.send_rc_control(0, 0, 0, 0)
        krok =12
    elif krok == 12:
        print('laduj')
        me.land()
        me.end()








    for i in range(len(contours_z)):
        for j in range(len(contours_c)):
            if ((calculate_area(contours_z[i],zielony)) > 6500 and ((calculate_area(contours_z[i],zielony))>(calculate_area(contours_c[j],czerwony))) and zn_c == False) and (krok != 4 or krok != 8 ):
                lower = np.array([38, 106, 67])
                upper = np.array([179, 255, 147])
                zn_z = True
                zn_c = False
                is_color_detected = True


            elif ((calculate_area(contours_c[j], czerwony)) > 6500 and ((calculate_area(contours_z[i],zielony))<(calculate_area(contours_c[j],czerwony))) and zn_z == False) and (krok != 4 or krok != 8 ):
                lower = np.array([0,186,61])
                upper = np.array([179,255,194])
                zn_c = True
                zn_z = False
                is_color_detected = True


    mask = cv2.inRange(imgHsv,lower,upper)
    result = cv2.bitwise_and(img,img, mask = mask)
    mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    imgBlur = cv2.GaussianBlur(result, (7, 7), 1)
    imgGray = cv2.cvtColor(imgBlur, cv2.COLOR_BGR2GRAY)
    threshold1 = cv2.getTrackbarPos("Threshold1", "Parameters")
    threshold2 = cv2.getTrackbarPos("Threshold2", "Parameters")
    imgCanny = cv2.Canny(imgGray, threshold1, threshold2)
    kernel = np.ones((5, 5))
    imgDil = cv2.dilate(imgCanny, kernel, iterations=1)
    getContours(imgDil, imgContour)
    display(imgContour)

    stack = stackImages(0.7,([img,result],[imgDil,imgContour]))

    cv2.imshow('Horizontal Stacking', stack)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        me.land()
        break

cap.release()
cv2.destroyAllWindows()