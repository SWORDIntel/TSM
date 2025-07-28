import time
import pickle
import grpc
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

def measure_search_time(stub, search_terms, operator=None):
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
    response = stub.EncryptedSearch(request)
    end_time = time.time()

    return end_time - start_time

async def run_benchmarks_async():
    print("Running benchmarks...")

    server_config = TSMServerPresets.grpc_server()
    manager = ServerManager()

    async with manager.managed_servers([server_config]):
        print("Server is running under manager.")

        channel = grpc.insecure_channel(f'localhost:{server_config.port}')
        stub = TSMService_pb2_grpc.TSMServiceStub(channel)

        # Wait for channel to be ready
        try:
            await channel.channel_ready()
        except grpc.aio.AioRpcError as e:
            print(f"Failed to connect to server: {e}", file=sys.stderr)
            return

        # Run benchmarks
        t_single = measure_search_time(stub, ["alpha"])
        print(f"Single search time: {t_single:.4f} seconds")

        # Example for boolean search (commented out until fully implemented)
        # t_and = measure_search_time(stub, ["alpha", "beta"], operator="AND")
        # print(f"Boolean AND search time: {t_and:.4f} seconds")

        # t_or = measure_search_time(stub, ["alpha", "gamma"], operator="OR")
        # print(f"Boolean OR search time: {t_or:.4f} seconds")

    print("Server shutdown complete")

def run_benchmarks():
    asyncio.run(run_benchmarks_async())

if __name__ == '__main__':
    run_benchmarks()
