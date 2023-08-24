# -*- coding: utf-8 -*-
import time
import Adafruit_ADS1x15
adc = Adafruit_ADS1x15.ADS1115()
bat_full=8768
bat_empty=6000
# Choose a gain of 1 for reading voltages from 0 to 4.09V.
# Or pick a different gain to change the range of voltages that are read:
#  – 2/3 = +/-6.144V
#  –   1 = +/-4.096V
#  –   2 = +/-2.048V
#  –   4 = +/-1.024V
#  –   8 = +/-0.512V
#  –  16 = +/-0.256V
# See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
bat_capacity=bat_full-bat_empty
GAIN = 2/3
def BatStat():
 while True:
  value = adc.read_adc(0, gain=GAIN)
  percent_of_bat=int(((bat_empty-value)/bat_capacity)*100)
#  time.sleep(0.5)
  if percent_of_bat<0:
      percent_of_bat=percent_of_bat * -1
      return percent_of_bat
  else:
      return 0
#print (BatStat())
