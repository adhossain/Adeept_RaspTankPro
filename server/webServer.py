#!/usr/bin/env/python
# File name   : server.py
# Production  : RaspTankPro
# Website     : www.adeept.com
# Author      : William
# Date        : 2020/03/17

import time
import threading
import move
import Adafruit_PCA9685
import os
import info
import RPIservo
from BatMon import *
import functions
import robotLight
import switch
import socket

#websocket
import asyncio
import websockets

import json
import app

OLED_connection = 1
try:
    import OLED
    screen = OLED.OLED_ctrl()
    screen.start()
    screen.screen_show(1, 'ADEEPT.COM')
except:
    OLED_connection = 0
    print('OLED disconnected')
    pass

functionMode = 0
speed_set = 100
rad = 0.5
turnWiggle = 60

scGear = RPIservo.ServoCtrl()
scGear.moveInit()

P_sc = RPIservo.ServoCtrl()
P_sc.start()

C_sc = RPIservo.ServoCtrl()
C_sc.start()

T_sc = RPIservo.ServoCtrl()
T_sc.start()

H_sc = RPIservo.ServoCtrl()
H_sc.start()

G_sc = RPIservo.ServoCtrl()
G_sc.start()

# modeSelect = 'none'
modeSelect = 'PT'

init_pwm = []
for i in range(16):
    init_pwm.append(scGear.initPos[i])

# init_pwm0 = scGear.initPos[0]
# init_pwm1 = scGear.initPos[1]
# init_pwm2 = scGear.initPos[2]
# init_pwm3 = scGear.initPos[3]
# init_pwm4 = scGear.initPos[4]


fuc = functions.Functions()
fuc.start()

curpath = os.path.realpath(__file__)
thisPath = "/" + os.path.dirname(curpath)

def servoPosInit():
    scGear.initConfig(0,init_pwm0,1)
    P_sc.initConfig(1,init_pwm1,1)
    T_sc.initConfig(2,init_pwm2,1)
    H_sc.initConfig(3,init_pwm3,1)
    G_sc.initConfig(4,init_pwm4,1)


def replace_num(initial,new_num):   #Call this function to replace data in '.txt' file
    global r
    newline=""
    str_num=str(new_num)
    with open(thisPath+"/RPIservo.py","r") as f:
        for line in f.readlines():
            if(line.find(initial) == 0):
                line = initial+"%s" %(str_num+"\n")
            newline += line
    with open(thisPath+"/RPIservo.py","w") as f:
        f.writelines(newline)


def FPV_thread():
    global fpv
    fpv=FPV.FPV()
    fpv.capture_thread(addr[0])


def ap_thread():
    os.system("sudo create_ap wlan0 eth0 Groovy 12345678")


def functionSelect(command_input, response):
    global functionMode
    if 'scan' == command_input:
        if OLED_connection:
            screen.screen_show(5,'SCANNING')
        if modeSelect == 'PT':
            radar_send = fuc.radarScan()
            print(radar_send)
            response['title'] = 'scanResult'
            response['data'] = radar_send
            time.sleep(0.3)

    elif 'findColor' == command_input:
        if OLED_connection:
            screen.screen_show(5,'FindColor')
        if modeSelect == 'PT':
            flask_app.modeselect('findColor')

    elif 'motionGet' == command_input:
        if OLED_connection:
            screen.screen_show(5,'MotionGet')
        flask_app.modeselect('watchDog')

    elif 'stopCV' == command_input:
        flask_app.modeselect('none')
        switch.switch(1,0)
        switch.switch(2,0)
        switch.switch(3,0)

    elif 'police' == command_input:
        if OLED_connection:
            screen.screen_show(5,'POLICE')
        RL.police()

    elif 'policeOff' == command_input:
        RL.pause()
        move.motorStop()

    elif 'automatic' == command_input:
        if OLED_connection:
            screen.screen_show(5,'Automatic')
        if modeSelect == 'PT':
            fuc.automatic()
        else:
            fuc.pause()

    elif 'automaticOff' == command_input:
        fuc.pause()
        move.motorStop()

    elif 'trackLine' == command_input:
        fuc.trackLine()
        if OLED_connection:
            screen.screen_show(5,'TrackLine')

    elif 'trackLineOff' == command_input:
        fuc.pause()

    elif 'steadyCamera' == command_input:
        if OLED_connection:
            screen.screen_show(5,'SteadyCamera')
        fuc.steady(C_sc.lastPos[4])

    elif 'steadyCameraOff' == command_input:
        fuc.pause()
        move.motorStop()


def switchCtrl(command_input, response):
    if 'Switch_1_on' in command_input:
        switch.switch(1,1)

    elif 'Switch_1_off' in command_input:
        switch.switch(1,0)

    elif 'Switch_2_on' in command_input:
        switch.switch(2,1)

    elif 'Switch_2_off' in command_input:
        switch.switch(2,0)

    elif 'Switch_3_on' in command_input:
        switch.switch(3,1)

    elif 'Switch_3_off' in command_input:
        switch.switch(3,0) 


def robotCtrl(command_input, response):
    global direction_command, turn_command
    if 'forward' == command_input:
        direction_command = 'forward'
        move.move(speed_set, 'forward', 'no', rad)
    
    elif 'backward' == command_input:
        direction_command = 'backward'
        move.move(speed_set, 'backward', 'no', rad)

    elif 'DS' in command_input:
        direction_command = 'no'
        move.move(speed_set, 'no', 'no', rad)


    elif 'left' == command_input:
        turn_command = 'left'
        move.move(speed_set, 'no', 'left', rad)

    elif 'right' == command_input:
        turn_command = 'right'
        move.move(speed_set, 'no', 'right', rad)

    elif 'TS' in command_input:
        turn_command = 'no'
        if direction_command == 'no':
            move.move(speed_set, 'no', 'no', rad)
        else:
            move.move(speed_set, direction_command, 'no', rad)


    elif 'lookleft' == command_input:
        P_sc.singleServo(0, 1, 3)

    elif 'lookright' == command_input:
        P_sc.singleServo(0, -1, 3)

    elif 'LRstop' in command_input:
        P_sc.stopWiggle()

    elif 'armup' == command_input:
        T_sc.singleServo(1, 1, 3)

    elif 'armdown' == command_input:
        T_sc.singleServo(1, -1, 3)

    elif 'armstop' in command_input:
    	T_sc.stopWiggle()

    elif 'handup' == command_input:
        H_sc.singleServo(2, 1, 3)

    elif 'handdown' == command_input:
        H_sc.singleServo(2, -1, 3)

    elif 'handstop' in command_input:
        H_sc.stopWiggle()

    elif 'grab' == command_input:
        G_sc.singleServo(3, -1, 3)

    elif 'loose' == command_input:
        G_sc.singleServo(3, 1, 3)

    elif 'cameraup' == command_input:
        C_sc.singleServo(4, 1, 3)

    elif 'cameradown' == command_input:
        C_sc.singleServo(4, -1, 3)

    elif 'camerastop' in command_input:
        C_sc.stopWiggle()


    elif 'stop' == command_input:
        G_sc.stopWiggle()

    elif 'home' == command_input:
        P_sc.moveServoInit([0])
        C_sc.moveServoInit([4])
        T_sc.moveServoInit([1])
        H_sc.moveServoInit([2])
        G_sc.moveServoInit([3])


def setPWM(data):
    global init_pwm
    action = data.split()[0]
    PWMnum = int(data.split()[1])

    if "SiLeft"  == action:
        print("xxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        init_pwm[PWMnum]+= 1
        scGear.setPWM(PWMnum, init_pwm[PWMnum])

    elif "SiRight" == action:
        init_pwm[PWMnum]-= 1
        scGear.setPWM(PWMnum, init_pwm[PWMnum])
    
    elif "PWMMS" == action:
        P_sc.initConfig(PWMnum, init_pwm[PWMnum], 1)
        replace_num("init_pwm" + str(PWMnum) + " = ",init_pwm[PWMnum] )


def configPWM(command_input, response):
    global init_pwm
    if 'SiLeft' in command_input or 'SiRight' in command_input or 'PWMMS' in command_input:
        setPWM(command_input)

    elif 'PWMINIT' == command_input:
        servoPosInit()

    elif 'PWMD' == command_input:
        init_pwm0,init_pwm1,init_pwm2,init_pwm3,init_pwm4=300,300,300,300,300
        scGear.initConfig(0,init_pwm0,1)
        replace_num('init_pwm0 = ', 300)

        P_sc.initConfig(1,300,1)
        replace_num('init_pwm1 = ', 300)

        T_sc.initConfig(2,300,1)
        replace_num('init_pwm2 = ', 300)

        H_sc.initConfig(3,300,1)
        replace_num('init_pwm3 = ', 300)

        G_sc.initConfig(4,300,1)
        replace_num('init_pwm4 = ', 300)


def update_code():
    # Update local to be consistent with remote
    projectPath = thisPath[:-7]
    with open(f'{projectPath}/config.json', 'r') as f1:
        config = json.load(f1)
        if not config['production']:
            print('Update code')
            # Force overwriting local code
            if os.system(f'cd {projectPath} && sudo git fetch --all && sudo git reset --hard origin/master && sudo git pull') == 0:
                print('Update successfully')
                print('Restarting...')
                os.system('sudo reboot')

def wifi_check():
    try:
        s =socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(("1.1.1.1",80))
        ipaddr_check=s.getsockname()[0]
        s.close()
        print(ipaddr_check)
        update_code()
        if OLED_connection:
            screen.screen_show(2, 'IP:'+ipaddr_check)
            screen.screen_show(3, 'AP MODE OFF')
    except:
        RL.pause()
        RL.setColor(0,255,64)
        ap_threading=threading.Thread(target=ap_thread)   #Define a thread for data receiving
        ap_threading.setDaemon(True)                          #'True' means it is a front thread,it would close when the mainloop() closes
        ap_threading.start()                                  #Thread starts
        if OLED_connection:
            screen.screen_show(2, 'AP Starting 10%')
        RL.setColor(0,16,50)
        time.sleep(1)
        if OLED_connection:
            screen.screen_show(2, 'AP Starting 30%')
        RL.setColor(0,16,100)
        time.sleep(1)
        if OLED_connection:
            screen.screen_show(2, 'AP Starting 50%')
        RL.setColor(0,16,150)
        time.sleep(1)
        if OLED_connection:
            screen.screen_show(2, 'AP Starting 70%')
        RL.setColor(0,16,200)
        time.sleep(1)
        if OLED_connection:
            screen.screen_show(2, 'AP Starting 90%')
        RL.setColor(0,16,255)
        time.sleep(1)
        if OLED_connection:
            screen.screen_show(2, 'AP Starting 100%')
        RL.setColor(35,255,35)
        if OLED_connection:
            screen.screen_show(2, 'IP:192.168.12.1')
            screen.screen_show(3, 'AP MODE ON')

async def check_permit(websocket):
    while True:
        recv_str = await websocket.recv()
        cred_dict = recv_str.split(":")
        if cred_dict[0] == "admin" and cred_dict[1] == "123456":
            response_str = "congratulation, you have connect with server\r\nnow, you can do something else"
            await websocket.send(response_str)
            return True
        else:
            response_str = "sorry, the username or password is wrong, please submit again"
            await websocket.send(response_str)

async def recv_msg(websocket):
    global speed_set, modeSelect
    move.setup()
    direction_command = 'no'
    turn_command = 'no'

    while True: 
        response = {
            'status' : 'ok',
            'title' : '',
            'data' : None
        }
        screen.screen_show(1, 'Battery:' + str(BatStat()) + '%')   #I found this While loop to run the code, to not make any new threads
        data = ''
        data = await websocket.recv()
        try:
            data = json.loads(data)
        except Exception as e:
            print('not A JSON')

        if not data:
            continue

        if isinstance(data,str):
            robotCtrl(data, response)

            switchCtrl(data, response)

            functionSelect(data, response)

            configPWM(data, response)

            if 'get_info' == data:
                response['title'] = 'get_info'
                response['data'] = [info.get_cpu_tempfunc(), info.get_cpu_use(), info.get_ram_info()]

            if 'wsB' in data:
                try:
                    set_B=data.split()
                    speed_set = int(set_B[1])
                except:
                    pass

            elif 'AR' == data:
                modeSelect = 'AR'
                screen.screen_show(4, 'ARM MODE ON')
                try:
                    fpv.changeMode('ARM MODE ON')
                except:
                    pass

            elif 'PT' == data:
                modeSelect = 'PT'
                screen.screen_show(4, 'PT MODE ON')
                try:
                    fpv.changeMode('PT MODE ON')
                except:
                    pass

            #CVFL
            elif 'CVFL' == data:
                flask_app.modeselect('findlineCV')

            elif 'CVFLColorSet' in data:
                color = int(data.split()[1])
                flask_app.camera.colorSet(color)

            elif 'CVFLL1' in data:
                pos = int(data.split()[1])
                flask_app.camera.linePosSet_1(pos)

            elif 'CVFLL2' in data:
                pos = int(data.split()[1])
                flask_app.camera.linePosSet_2(pos)

            elif 'CVFLSP' in data:
                err = int(data.split()[1])
                flask_app.camera.errorSet(err)

            elif 'defEC' in data:#Z
                fpv.defaultExpCom()

        elif(isinstance(data,dict)):
            if data['title'] == "findColorSet":
                color = data['data']
                flask_app.colorFindSet(color[0],color[1],color[2])

        if not functionMode:
            if OLED_connection:
                screen.screen_show(5,'Functions OFF')
        else:
            pass

        print(data)
        response = json.dumps(response)
        await websocket.send(response)

async def main_logic(websocket, path):
    await check_permit(websocket)
    await recv_msg(websocket)

if __name__ == '__main__':
    switch.switchSetup()
    switch.set_all_switch_off()

    HOST = ''
    PORT = 10223                              #Define port serial 
    BUFSIZ = 1024                             #Define buffer size
    ADDR = (HOST, PORT)

    global flask_app
    flask_app = app.webapp()
    flask_app.startthread()

    try:
        RL=robotLight.RobotLight()
        RL.start()
        RL.breath(70,70,255)
    except:
        print('Use "sudo pip3 install rpi_ws281x" to install WS_281x package\n使用"sudo pip3 install rpi_ws281x"命令来安装rpi_ws281x')
        pass

    while  1:
        wifi_check()
        try:                  #Start server,waiting for client
            start_server = websockets.serve(main_logic, '0.0.0.0', 8888)
            asyncio.get_event_loop().run_until_complete(start_server)
            print('waiting for connection...')
            # print('...connected from :', addr)
            break
        except Exception as e:
            print(e)
            RL.setColor(0,0,0)

        try:
            RL.setColor(0,80,255)
        except:
            pass
    try:
        # RL.pause()
        # RL.setColor(0,255,64)
        asyncio.get_event_loop().run_forever()
    except Exception as e:
        print(e)
        RL.setColor(0,0,0)
        move.destroy()
