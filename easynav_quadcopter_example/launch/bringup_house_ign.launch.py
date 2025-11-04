import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    package_name = 'easynav_quadcopter_example'

    # World and model paths
    world_file = os.path.join(
        get_package_share_directory(package_name),
        'worlds',
        'house_world.sdf'
    )
    models_path = os.path.join(
        get_package_share_directory(package_name),
        'models'
    )

    # Set IGN_GAZEBO_RESOURCE_PATH so Gazebo can locate the models
    set_gazebo_resource_path = SetEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=models_path
    )

    # Include the Ignition Gazebo launch file
    ign_gazebo_launch = os.path.join(
        get_package_share_directory('ros_ign_gazebo'),
        'launch',
        'ign_gazebo.launch.py'
    )
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(ign_gazebo_launch),
        launch_arguments=[('gz_args', f' -r -v 1 {world_file}')]
    )

    # ROS–Gazebo bridge node
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': os.path.join(
                get_package_share_directory(package_name),
                'config',
                'ros_gz_x3_bridge.yaml'
            ),
        }],
        output='screen'
    )

    # Launch RViz with a custom configuration
    rviz_config_file = os.path.join(
        get_package_share_directory(package_name),
        'rviz',
        'view.rviz'
    )
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        output='screen'
    )

    # Static transform between x3/base_link and camera_frame_rgb
    static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_camera',
        arguments=[
            # Translation (x, y, z) and rotation (roll, pitch, yaw)
            '0.0', '0.0', '0.1',     # Camera 10 cm above base_link
            '0.0', '0.0', '0.0',     # No rotation
            'x3/X3/base_link', 'camera_frame_rgb'
        ],
        output='screen'
    )

    # OctoMap server node for 3D occupancy mapping
    octomap_node = Node(
        package='octomap_server',
        executable='octomap_server_node',
        name='octomap_server',
        output='screen',
        parameters=[
            {'resolution': 0.1},
            {'frame_id': 'odom'},
            {'sensor_model.max_range': 5.0}
        ],
        remappings=[
            ('cloud_in', '/camera/points')
        ]
    )

    return LaunchDescription([
        set_gazebo_resource_path,
        gazebo_launch,
        bridge,
        octomap_node,
        rviz_node,
        static_tf
    ])


