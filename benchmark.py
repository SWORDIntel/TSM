import time
import pickle
import grpc.aio as aio
from concurrent import futures
import sys
import os
import asyncio
import statistics

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'mock_server')))
import TSMService_pb2
import TSMService_pb2_grpc
from homomorphic_search import HomomorphicSearchPrototype
from server_manager import ServerManager, TSMServerPresets

async def measure_search_time(stub, search_terms, operator=None):
    print(f"Measuring search time for terms: {search_terms} with operator: {operator}")
    search_prototype = HomomorphicSearchPrototype()
    encrypted_queries = [
        pickle.dumps(search_prototype.generate_encrypted_query(search_prototype.public_key.encrypt(hash(term))))
        for term in search_terms
    ]
    request = TSMService_pb2.EncryptedSearchRequest(
        encrypted_queries=[q.decode('latin-1') for q in encrypted_queries],
        operator=TSMService_pb2.EncryptedSearchRequest.AND if operator == "AND" else TSMService_pb2.EncryptedSearchRequest.OR
    )

    start_time = time.time()
    response = await stub.EncryptedSearch(request)
    end_time = time.time()

    return end_time - start_time

async def run_benchmarks_async():
    print("Running benchmarks...")

    server_config = TSMServerPresets.grpc_server()
    manager = ServerManager()

    print("Starting server manager...")
    async with manager.managed_servers([server_config]) as svr_manager:
        print("Server is running under manager.")

        print(f"Connecting to server at localhost:{server_config.port}...")
        channel = aio.insecure_channel(f'localhost:{server_config.port}')
        stub = TSMService_pb2_grpc.TSMServiceStub(channel)

        # Wait for channel to be ready
        print("Waiting for channel to be ready...")
        try:
            await asyncio.wait_for(channel.channel_ready(), timeout=10.0)
            print("Channel is ready.")
        except asyncio.TimeoutError:
            print("Failed to connect to server: channel ready timeout", file=sys.stderr)
            return
        except grpc.RpcError as e:
            print(f"Failed to connect to server: {e}", file=sys.stderr)
            return

        # Run benchmarks
        print("Running single search benchmark...")
        t_single = await measure_search_time(stub, ["alpha"])
        print(f"Single search time: {t_single:.4f} seconds")

        # Example for boolean search (commented out until fully implemented)
        # print("Running AND search benchmark...")
        # t_and = await measure_search_time(stub, ["alpha", "beta"], operator="AND")
        # print(f"Boolean AND search time: {t_and:.4f} seconds")

        # print("Running OR search benchmark...")
        # t_or = await measure_search_time(stub, ["alpha", "gamma"], operator="OR")
        # print(f"Boolean OR search time: {t_or:.4f} seconds")

    print("Server shutdown complete")

def run_benchmarks():
    asyncio.run(run_benchmarks_async())

if __name__ == '__main__':
    run_benchmarks()
