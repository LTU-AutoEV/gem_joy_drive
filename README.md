# gem_joy_drive
Drive the GEM vehicle using a Joystick with a python ROS node

# Directions
To run in the vehicle with DBW installed:

'roslaunch gem_joy_drive gem_joy_drive_dbw.launch sys:=true'

To run without CAN network for testing

'roslaunch gem_joy_drive gem_joy_drive_dbw.launch'

# Joystick mappings

- Enable tigger: JOY_BUTTON_R (enable trigger must be depressed for any joystick input)

- Steering: JOY_AXES_CROSS_LR
- Brake: JOY_TRIGGER_L
- Throttle: JOY_TRIGGER_R