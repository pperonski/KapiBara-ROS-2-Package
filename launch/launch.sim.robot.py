import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import Shutdown

from launch_ros.actions import Node
import xacro

def generate_launch_description():

    # Specify the name of the package and path to xacro file within the package
    pkg_name = 'kapibara'
    file_subpath = 'description/kapibara.urdf.xacro'
    
    package_share_dir = get_package_share_directory(pkg_name)

    # Use xacro to process the file
    xacro_file = os.path.join(package_share_dir,file_subpath)
    robot_description_raw = xacro.process_file(xacro_file,mappings={'sim_mode' : 'true','robot_name' : 'KapiBara'}).toxml()
    
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

    mujoco_control = Node(
            package="mujoco_ros2_control",
            executable="ros2_control_node",
            emulate_tty=True,
            namespace="KapiBara",
            output="both",
            parameters=[
                {"use_sim_time": True},
                controller_cfg_file_sim
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
    
    # Run the node
    return LaunchDescription([
        mujoco_control,
        node_robot_state_publisher,
        imu_spawner,
        diff_drive_spawner,
        joint_broad_spawner,
        ears_controller_spawner,
    ])


