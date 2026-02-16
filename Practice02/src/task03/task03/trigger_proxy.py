import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class TriggerProxy(Node):
    def __init__(self) -> None:
        super().__init__('trigger_proxy')

        self.declare_parameter('service_name', '/trigger_service')
        self.declare_parameter('default_string', 'No service available')

        self.service_name = self.get_parameter('service_name').get_parameter_value().string_value
        self.default_string = self.get_parameter('default_string').get_parameter_value().string_value

        self.stored_string = self.default_string

        self.client = self.create_client(Trigger, '/spgc/trigger')
        self.service = self.create_service(Trigger, self.service_name, self.handle_service)

    def fetch_remote_string(self) -> None:
        if not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('/spgc/trigger not available, using default string')
            return

        request = Trigger.Request()
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)

        if not future.done():
            self.get_logger().info('/spgc/trigger call timed out, using default string')
            return

        result = future.result()
        if result is None:
            self.get_logger().info('/spgc/trigger call failed, using default string')
            return

        self.stored_string = result.message
        self.get_logger().info('Stored string updated from /spgc/trigger')

    def handle_service(self, _request: Trigger.Request, response: Trigger.Response) -> Trigger.Response:
        response.success = True
        response.message = self.stored_string
        return response


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TriggerProxy()
    node.fetch_remote_string()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
