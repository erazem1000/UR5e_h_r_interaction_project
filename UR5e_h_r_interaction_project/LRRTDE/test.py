from LRRTDE import LRRTDE

#outputList = ["timestamp","actual_q","actual_TCP_pose","actual_TCP_speed","actual_TCP_force","actual_digital_output_bits","target_current","target_moment","actual_current"]
#outputList = ["timestamp","actual_q","actual_TCP_pose","actual_TCP_speed"]

outputList = ["timestamp","actual_q","actual_qd","actual_TCP_pose","actual_TCP_speed"]

freq = 500
robot_ip = "192.168.65.244"
robot_port = 30004
protocol_ver = 2

fw_ip = "localhost"
fw_port = 21000

#fw_ip = "192.168.65.239"
#fw_port = 21000




if __name__ == "__main__":
    print("main start")
    RTDE = LRRTDE()

    RTDE.connect(robot_ip, robot_port, protocol_ver)
    RTDE.setOutputs(outputList, freq)

    RTDE.start(fw_ip, fw_port)
    print("RTDE.start")

    input("Press enter to stop the echo server...")


    RTDE.stop()
    print("RTDE.stop")

