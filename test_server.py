
import grpc
from concurrent import futures
import time
import sys
import os

# Simple test service
class TestService:
    def Test(self, request, context):
        return request

def serve(port=50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    # Add a dummy service to make it a valid gRPC server
    # A generic add_generic_rpc_handlers can be used if no specific service is available
    class DummyGenericRpcHandler(grpc.GenericRpcHandler):
        def service(self, handler_call_details):
            return None
    server.add_generic_rpc_handlers((DummyGenericRpcHandler(),))
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"Test server started on port {port}", flush=True)

    # Keep server running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        server.stop(0)

if __name__ == '__main__':
    port = 50051
    # Check for --port argument
    if '--port' in sys.argv:
        try:
            port_index = sys.argv.index('--port') + 1
            if port_index < len(sys.argv):
                port = int(sys.argv[port_index])
        except (ValueError, IndexError):
            print("Invalid port argument. Using default 50051.")

    # A simple pid file mechanism for cleanup in tests
    pid = os.getpid()
    with open(f"test_server_{port}.pid", "w") as f:
        f.write(str(pid))

    serve(port)
