#!/usr/bin/python

import RPi.GPIO as rpi
from smbus import SMBus
import time

# constants
ADDR_I2C = 0x54		# fixed i2c address of sn3218 circuit
ADDR_OUT = 0x00 	# enable output by writing 0x01/1
ADDR_BANK = 0x13	# first bank of 6, others at 0x14 and 0x15
ADDR_LED0 = 0x01	# first led address, up to 0x12
ADDR_UPDATE = 0x16	# update state by writing 0xff/255

class Led:
  """led object"""
  
  # light
  light = [0] * 18
  
  # index   w   b   g   y   o   r
  order = ( 9,  4,  5,  8,  7,  6,  # arm0
           10, 11, 13, 15, 16, 17,  # arm1
           12, 14,  3,  2,  1 , 0)  # arm2

  def __init__(self, index):
    """led at the given index [0-17], in -> out, starting top clockwise"""
    self.index = Led.order[index]
    self.lit(0)

  def lit(self, value):
    """set led to specified value"""
    Led.light[self.index] = value

  def status(self):
    """get status of led"""
    return "led[%d]=%d" % (Led.order.index(self.index)%6, Led.light[self.index])

class Control:
  """PiGlow controller"""

  # list of leds
  leds = [Led(i) for i in range(18)]

  # colors
  colors = ("white", "blue", "green", "yellow", "orange", "red")
  
  # intensities gradient
  intensities = [0x01, 0x02, 0x04, 0x08, 0x10, 0x18,
                 0x20, 0x30, 0x40, 0x50, 0x60, 0x70,
                 0x80, 0x90, 0xA0, 0xC0, 0xE0, 0xFF]
  
  def __init__(self):
    """update the condition of the leds"""
    if rpi.RPI_REVISION == 1: Control.bus = SMBus(0)
    else: Control.bus = SMBus(1)

    # enable output
    self.__write(ADDR_OUT, [0x01])

    # enabled leds (i.e., for addresses 0x13 thru 0x15)
    self.__write(ADDR_BANK, [0xff, 0xff, 0xff])

  def __getitem__(self, idx): return Control.leds[idx]
    
  def arm(self, arm):
    """get an arm of leds, indexed 0 from top going clockwise"""
    idx = arm * 6
    return Control.leds[idx:idx+6]

  def circle(self, circle):
    """get a circle of leds, indexed 0 from center"""
    return [Control.leds[i] for i in range(circle, 18, 6)]

  def led(self, arm, color):
    """get the led with the given color on the specified arm"""
    return Control.leds[arm*6 + Control.colors.index(color)]

  def update(self):
    """update the leds against the controller"""
    #[self.__write(led.addr, [led.lit]) for led in Control.leds]
    self.__write(ADDR_LED0, Led.light)
    self.__update()

  def status(self):
    """show a status of all leds"""
    print ("%s" * 6) % tuple([s.rjust(12) for s in Control.colors])
    for arm in range(3):
      print "arm%d:" % arm,
      print ("%s" * 6) % tuple([led.status().ljust(12) for led in self.arm(arm)])
    print ""

  def __update(self):
    """perform an update to commit transaction"""
    self.__write(ADDR_UPDATE, [0xff])

  def __write(self, addr, vals):
    """write a list of values starting at address"""
    Control.bus.write_i2c_block_data(ADDR_I2C, addr, vals)


# run this script to try out the vortex routine
if __name__ == "__main__":
  def vortex(out):
    c = Control()
    bright = [c.intensities[i] for i in range(0, 18, 3)]
    bright[0] = 0
    glow = range(6)
    if not out: glow.reverse()
    while True:
      for cir in range(6):
        for led in c.circle(cir): led.lit(c.intensities[glow[cir]])
        glow[cir] -= 1
        if glow[cir] == -1: glow[cir] = 5
      c.update()
      time.sleep(0.1)

  # execute incoming
  try: vortex(False)
  except:
    # turn off all leds
    for led in Control.leds: led.lit(0)
    Control().update()
    