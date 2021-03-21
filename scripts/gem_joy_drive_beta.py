#!/usr/bin/env python

import rospy
from sensor_msgs.msg import Joy
from std_msgs.msg import Empty
from dbw_polaris_msgs.msg import Gear, GearCmd, GearReject, GearReport
from dbw_polaris_msgs.msg import BrakeCmd, BrakeReport
from dbw_polaris_msgs.msg import ThrottleCmd, ThrottleReport
from dbw_polaris_msgs.msg import SteeringCmd, SteeringReport
       

# Joystick mapping
JOY_BUTTON_A = 0
JOY_BUTTON_B = 1
JOY_BUTTON_X = 2
JOY_BUTTON_Y = 3
JOY_BUTTON_L = 4
JOY_BUTTON_R = 5

JOY_AXES_LEFT_STICK_LR = 0
JOY_AXES_LEFT_STICK_UD = 1
JOY_AXES_RIGHT_STICK_LR = 3
JOY_AXES_RIGHT_STICK_UD = 4
JOY_AXES_CROSS_LR = 6
JOY_AXES_CROSS_UD = 7

JOY_TRIGGER_L = 2  # Brake (1 -> -1 = max)
JOY_TRIGGER_R = 5  # Throttle (1 -> -1 = max)


# GEM Gears
PARK = 0
NEUTRAL = 1
DRIVE = 2
REVERSE = 3
GEAR_DISP = ['Park','Neutral','Drive','Reverse']

# GemDrive class definition
class GemDrive():
    def __init__(self):
        """GemDrive to enable joystick GEM driving"""

        # Set joystick enable flag
        self.joy_enable = False
        
        # Define the throttle, braking and steering commands
        self.msg_throttle_cmd = ThrottleCmd()
        self.msg_brake_cmd = BrakeCmd()
        self.msg_steering_cmd = SteeringCmd()
        self.initialize_commands()
        
        # Initialize drive-by-wire reporting messages
        self.msg_throttle_report = ThrottleReport()
        self.msg_throttle_report_ready = False
        self.msg_gear_report = GearReport()
        self.msg_gear_report_ready = False
        self.msg_steering_report = SteeringReport()
        self.msg_steering_report_ready = False

        # Initialize vehicle state
        self.gear = NEUTRAL
        self.throttle_initialized = False
        self.brake_initialized = False

        # Publishers and subscribers
        self.pub_throttle_cmd = rospy.Publisher('/vehicle/throttle_cmd', ThrottleCmd, queue_size=1)
        self.pub_brake_cmd = rospy.Publisher('/vehicle/brake_cmd', BrakeCmd, queue_size=1)
        self.pub_steering_cmd = rospy.Publisher('/vehicle/steering_cmd', SteeringCmd, queue_size=1)
        self.pub_enable_cmd =  rospy.Publisher('/vehicle/enable', Empty, queue_size=1)
        self.pub_disable_cmd =  rospy.Publisher('/vehicle/disable', Empty, queue_size=1)
        
        rospy.Subscriber("joy", Joy, self.joy_callback, queue_size=1)
        rospy.Subscriber('/vehicle/throttle_report', ThrottleReport, self.recv_throttle)
        rospy.Subscriber('/vehicle/gear_report', GearReport, self.recv_gear)
        rospy.Subscriber('/vehicle/steering_report', SteeringReport, self.recv_steering)

        # Define ROS rate
        self.rate = rospy.Rate(50)

        #rospy.spin()
        
        # Loop and publish commands to vehicle
        while not rospy.is_shutdown():
            # Publish commands
            self.pub_throttle_cmd.publish(self.msg_throttle_cmd)
            self.pub_brake_cmd.publish(self.msg_brake_cmd)
            self.pub_steering_cmd.publish(self.msg_steering_cmd)

            msg = Empty()
            if( self.joy_enable):
                self.pub_enable_cmd.publish(msg)
            else:
                self.pub_disable_cmd.publish(msg)

            self.rate.sleep()
            

        #    if( self.joy_enable ):
        #        self.pub_throttle_cmd.publish(self.msg_throttle_cmd)
        #        self.pub_brake_cmd.publish(self.msg_brake_cmd)
        #        self.pub_steering_cmd.publish(self.msg_steering_cmd)
                #self.initialize_commands()
                
        #    self.rate.sleep()
        return
       

    #####################
    # Joystick callback
    #####################
    def joy_callback(self, data):

       
        # Check the enable button
        if( data.buttons[JOY_BUTTON_R] != 1.0 ):
            self.initialize_commands()
            self.joy_enable = False

            self.msg_throttle_cmd.enable = False
            self.msg_throttle_cmd.pedal_cmd = 0.0

            self.msg_brake_cmd.enable = False
            self.msg_brake_cmd.pedal_cmd = 0.0
            
            #self.msg_steering_cmd.enable = False
            
        else:
            self.joy_enable = True
        
            if( ~self.throttle_initialized ):
                if( data.axes[JOY_TRIGGER_R] != 0.0 ):
                    self.throttle_initialized = True
                
            if( ~self.brake_initialized ):
                if( data.axes[JOY_TRIGGER_L] != 0.0 ):
                    self.brake_initialized = True
            
            # Check for throttle input
            throttle_cmd = 0.0
            if( self.throttle_initialized ):
                throttle_cmd = 0.25 * (1.0 - data.axes[JOY_TRIGGER_R] ) / 2.0
                
            # Check for braking input
            brake_cmd = 0.0
            if( self.brake_initialized ):
                brake_cmd = 0.5 * (1.0 - data.axes[JOY_TRIGGER_L] ) / 2.0

            # Check for steering input
            steering_cmd = data.axes[JOY_AXES_RIGHT_STICK_LR]
            
            # Check for gear selection
            set_gear = False
            if( data.buttons[JOY_BUTTON_A] ):
                self.gear = DRIVE
                set_gear = True
            if( data.buttons[JOY_BUTTON_B] ):
                self.gear = REVERSE
                set_gear = True
            if( data.buttons[JOY_BUTTON_X] ):
                self.gear = PARK
                set_gear = True
            if( data.buttons[JOY_BUTTON_Y] ):
                self.gear = NEUTRAL
                set_gear = True
        
            if( set_gear ):
                rospy.loginfo(' ==> Set gear to %s' %
                              GEAR_DISP[self.gear] )

            # Output state
            #rospy.loginfo('Brake/Throttle/Steer = %s: (%5.1f%%, %5.1f%%, %5.1f%%)' %
            #              (GEAR_DISP[self.gear][0],
            #               brake_cmd*100,
            #               throttle_cmd*100,
            #               steering_cmd*100 ) )

            # Update commands
            self.msg_throttle_cmd.pedal_cmd = throttle_cmd
            self.msg_throttle_cmd.enable = True
            self.msg_brake_cmd.pedal_cmd = brake_cmd
            self.msg_brake_cmd.enable = True
            self.msg_steering_cmd.steering_wheel_torque_cmd = steering_cmd*SteeringCmd.TORQUE_MAX/5
            self.msg_steering_cmd.enable = True


        return


    def initialize_commands(self):
        self.msg_throttle_cmd.pedal_cmd = 0.0
        # CMD_NONE || CMD_PEDAL=0.20 to 0.80 || CMD_PERCENT=0 to 1
        self.msg_throttle_cmd.pedal_cmd_type = ThrottleCmd.CMD_PERCENT
        self.msg_throttle_cmd.enable = False
        self.msg_throttle_cmd.clear = False
        self.msg_throttle_cmd.ignore = False
        self.msg_throttle_cmd.count = 0

        self.msg_brake_cmd.pedal_cmd = 0.0
        # CMD_PERCENT=0 to 1 ||CMD_TORQUE=0 to 8000Nm || CMD_TORQUE_RQ 0 to 8000 Nm, closed-loop
        self.msg_brake_cmd.pedal_cmd_type = BrakeCmd.CMD_PERCENT  
        self.msg_brake_cmd.enable = False
        self.msg_brake_cmd.clear = False
        self.msg_brake_cmd.ignore = False
        self.msg_brake_cmd.count = 0

        self.msg_steering_cmd.steering_wheel_angle_cmd = 0.0
        self.msg_steering_cmd.steering_wheel_angle_velocity = 0.0
        self.msg_steering_cmd.steering_wheel_torque_cmd = 0.0
        # CMD_ANGLE || CMD_TORQUE
        self.msg_steering_cmd.cmd_type = SteeringCmd.CMD_TORQUE 
        self.msg_steering_cmd.enable = False
        self.msg_steering_cmd.clear = False
        self.msg_steering_cmd.ignore = False
        self.msg_steering_cmd.calibrate = False
        self.msg_steering_cmd.quiet = False
        self.msg_steering_cmd.count = 0

        return
    
    
    def recv_throttle(self, msg):
        self.msg_throttle_report = msg
        self.msg_throttle_report_ready = True

    def recv_gear(self, msg):
        self.msg_gear_report = msg
        self.msg_gear_report_ready = True

    def recv_steering(self, msg):
        self.msg_steering_report = msg
        self.msg_steering_report_ready = True


# Main function.
if __name__ == '__main__':
    
    # Initialize the node and name it.
    rospy.init_node('gem_joy_drive_node')
    print "GEM joy drive node initialized"
    
    # Start tester
    try:
        GemDrive()
    except rospy.ROSInterruptException:
        pass
