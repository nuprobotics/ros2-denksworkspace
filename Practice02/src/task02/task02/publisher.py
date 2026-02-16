import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class PublisherNode(Node):
    def __init__(self) -> None:
        super().__init__('publisher')

        self.declare_parameter('topic_name', '/spgc/receiver')
        self.declare_parameter('text', 'Hello, ROS2!')

        topic_name = self.get_parameter('topic_name').get_parameter_value().string_value
        self.text = self.get_parameter('text').get_parameter_value().string_value

        self.publisher = self.create_publisher(String, topic_name, 10)
        self.timer = self.create_timer(1.0, self.publish_message)

    def publish_message(self) -> None:
        msg = String()
        msg.data = self.text
        self.publisher.publish(msg)
        self.get_logger().info(msg.data)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = PublisherNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
