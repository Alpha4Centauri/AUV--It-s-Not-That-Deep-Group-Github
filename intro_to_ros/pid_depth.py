#!/usr/bin/env python3

#~/ardupilot/Tools/autotest/sim_vehicle.py --vehicle=ArduSub --aircraft="bwsibot" -L RATBeach --out=udp:YOUR_COMPUTER_IP:14550
#ros2 launch /home/kenayosh/auvc_ws/src/AUV-Group-Github/launch/_.yaml

#cd ~/auvc_ws
#colcon build --symlink-install
#source ~/auvc_ws/install/setup.zsh

#ros2 topic list
#ros2 topic type /your/topic
#ro2 topic echo /your/topic :)))))
#ros2  interface show your_msg_library/msg/YourMessageType
#ros2 topic pub PID/desired_depth mavros_msgs/msg/Altitude "{relative: 0.8}" 

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from mavros_msgs.msg import ManualControl, Altitude
import numpy as np

import matplotlib.pyplot as plt


class PIDdepthNode(Node):
    def __init__(self):
        super().__init__('depth_node')
        #subscribers/publishers for necessary topics
        self.move_publisher = self.create_publisher(
            ManualControl,
            'bluerov2/manual_control',
            10
        )
        self.depth_subscriber = self.create_subscription(
            Altitude,
            'bluerov2/depth',
            self.depth_callback,
            10
        )

        self.desired_depth_subscriber = self.create_subscription(
            Altitude,
            'PID/desired_depth',
            self.desired_depth_callback,
            10
        )
        """
        PID CONSTANTS
        """

        # self.kp = 60
        # self.ki = 7
        # self.kd = 27
        
        # Masking tape robot/double O/4lights
        self.kp = 47
        self.ki = 7
        self.kd = 18
        
        # # AUV with the sticker
        # self.kp = 55
        # self.ki = 7
        # self.kd = 15
        
        self.max_integral = 4.0
        self.min_output = -100.0
        self.max_output = 100.0
        self.integral = 0.0
        self.previous_error = 0.0
        """"""
        self.get_logger().info('starting publisher node')
        #self.pid_yaw = PIDController(0.5, 0.1, 0.05, 1.0, -50, 50)
        """
        tracking constants
        """
        self.depth = float()
        self.desired_depth = None
        self.prev_time = None
        
        self.array = np.array([])

    def compute(self, error, dt):        
        """
        computes and logs the correction power based on the angle error and angular velocity in rad/s as derivative
        """
        #tracking
        self.array = np.append(self.array, [error])
        #integral calc
        self.integral += error*dt
        self.integral = max(min(self.integral, self.max_integral), -self.max_integral)
        #derivative calc
        derivative = (error - self.previous_error) / dt
        #p and summing errors
        proportional = self.kp * error
        output = proportional + (self.ki * self.integral) + (self.kd * derivative)
        # self.get_logger().info(f'\n Kp: {proportional} Ki: {self.ki * self.integral} Kd: {self.kd *derivative}')
        #updating error and clamping outputs
        output = max(min(output, self.max_output), self.min_output)
        self.previous_error = error
        return output

    def depth_callback(self, msg):
        """gets timestamp in secs and nanosecs from subscriber as well as depth in meters"""
        self.depth = msg.relative
        self.timestamp = msg.header.stamp.sec + 1e-09*msg.header.stamp.nanosec
        # self.get_logger().info("DLKFSJFS:DFKJF")
        if self.prev_time != None and self.desired_depth != None:
            self.calc_publish_vertical()
        self.prev_time = self.timestamp
        # self.get_logger().info(f'Depth: {self.depth}, Timestamp: {self.timestamp}')


    def desired_depth_callback(self, msg):
        """gets desired depth in m from subscriber"""
        self.desired_depth = msg.relative        
        
    def calc_publish_vertical(self):
        """publishes vertical movement based on desired depth and ouput from pid"""
        #checking if depth has been recieved and a dt has been produced
        #self.get_logger().info("DEPTH")
        
        if self.depth is not None and self.timestamp - self.prev_time > 0:
            depth_correction = self.compute(self.depth - self.desired_depth, self.timestamp - self.prev_time)
            movement = ManualControl()
            movement.x = np.inf
            movement.y = np.inf
            movement.r = np.inf
            movement.z = depth_correction
            # self.get_logger().info(f'\n DEPTHHHHCurrent Power: {depth_correction}/100\nDepth: {self.depth}')
            
            self.move_publisher.publish(movement)


def main(args=None):
    rclpy.init(args=args)
    move_node = PIDdepthNode()
    try:
        rclpy.spin(move_node)
    except KeyboardInterrupt:
        print('\nKeyboardInterrupt received, shutting down...')
    finally:
        x = np.arange(0,len(move_node.array))

        plt.plot(x,move_node.array)
        plt.savefig("/home/kenayosh/auvc_ws/src/AUV-Group-Github/intro_to_ros/images/depth_err.png")
        
        move_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
if __name__ == '__main__':
    main()


"""- node:
    pkg: "intro_to_ros"
    exec: "pid_depth"
    name: "pid_depth"
    namespace: """""

