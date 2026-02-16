import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Receiver(Node):
    def __init__(self) -> None:
        super().__init__('receiver')
        self.create_subscription(String, '/spgc/sender', self.listener_callback, 10)

    def listener_callback(self, msg: String) -> None:
        self.get_logger().info(msg.data)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = Receiver()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
