import os
import logging
import subprocess
from ament_index_python.packages import get_package_share_directory,get_package_prefix
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription,TimerAction,RegisterEventHandler,Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource

from launch_ros.actions import Node
import xacro
import math

def generate_launch_description():

    # Specify the name of the package and path to xacro file within the package
    pkg_name = 'kapibara'
    file_subpath = 'description/kapibara.urdf.xacro'
    
    package_share_dir = get_package_share_directory(pkg_name)


    # Use xacro to process the file
    xacro_file = os.path.join(package_share_dir,file_subpath)
    xacro_file_out = './kapibara1.urdf.xacro'
    mujoco_model_output = './model_output'
    robot_description_raw = xacro.process_file(xacro_file,mappings={'sim_mode' : 'true','robot_name' : 'KapiBara'}).toxml()
    
    with open(xacro_file_out, 'w+') as file:
        file.write(robot_description_raw)
    
    logging.info(f"Starting conversion of xacro to mujoco model: {mujoco_model_output}")
    subprocess.run([
            "ros2", "run", "mujoco_ros2_control", "robot_description_to_mjcf.sh", 
            "-u", xacro_file_out,
            "-o", mujoco_model_output,
            "--save_only"
        ], check=True)
    
    controller_cfg_file = os.path.join(package_share_dir,'config','my_controllers.yaml')
    controller_cfg_file_sim = os.path.join(package_share_dir,'config','my_controllers_sim.yaml')
    
    # Configure the node
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        namespace = 'KapiBara',
        parameters=[{'robot_description': robot_description_raw,
        'use_sim_time': True}] # add other parameters here if required
    )
    
    mujoco_urdf_conv =  Node(
            package="mujoco_ros2_control",
            executable="robot_description_to_mjcf.sh",
            output="both",
            emulate_tty=True,
            arguments=[
                        "--robot_description",
                        "KapiBara/robot_description",
                       "-m", mujoco_model_output+'/mujoco_description.xml',
                       "--publish_topic",
                        "/mujoco_robot_description"],
        )

    mujoco_control = Node(
            package="mujoco_ros2_control",
            executable="ros2_control_node",
            emulate_tty=True,
            namespace="KapiBara",
            output="both",
            parameters=[
                {"use_sim_time": True},
                controller_cfg_file
            ],
            remappings=(
                [("~/robot_description", "/KapiBara/robot_description")] if os.environ.get("ROS_DISTRO") == "humble" else []
            ),
            on_exit=Shutdown(),
        )
    
    imu_spawner = Node(
        package="controller_manager",
        executable="spawner",
        namespace="KapiBara",
        arguments=["imu_sensor_broadcaster",'--controller-manager-timeout','240'],
    )
    
    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        namespace="KapiBara",
        arguments=["motors",'--controller-manager-timeout','240'],
    )

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        namespace="KapiBara",
        arguments=["joint_broad",'--controller-manager-timeout','240'],
    )
    
    ears_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        namespace="KapiBara",
        arguments=["ears_controller",'--controller-manager-timeout','240'],
    )

    emotions = Node(
        package="emotion_estimer",
        executable="estimator.py",
        namespace="KapiBara",
        parameters=[{
            "sim":True
        }]
    )
    
    mic = Node(
        package="microphone",
        executable="mic.py",
        namespace = 'KapiBara',
        arguments=[],
        parameters=[{"channels":2,"sample_rate":44100,"chunk_size":4096,"device_id":5}],
        output='screen'
    )
    
    # Run the node
    return LaunchDescription([
        mujoco_control,
        node_robot_state_publisher,
        imu_spawner,
        diff_drive_spawner,
        joint_broad_spawner,
        ears_controller_spawner,
        mic,
    ])


