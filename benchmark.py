import time
import pickle
import grpc
from concurrent import futures
import sys
import os
import threading
import statistics

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'mock_server')))
import TSMService_pb2
import TSMService_pb2_grpc
from homomorphic_search import HomomorphicSearchPrototype
from mock_server.server import TSMService

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

def run_benchmarks():
    print("Running benchmarks...")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    TSMService_pb2_grpc.add_TSMServiceServicer_to_server(TSMService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    time.sleep(10)

    channel = grpc.insecure_channel('localhost:50051')
    stub = TSMService_pb2_grpc.TSMServiceStub(channel)

    # Run benchmarks
    t_single = measure_search_time(stub, ["alpha"])
    print(f"Single search time: {t_single:.4f} seconds")

    server.stop(0)
    print("Server shutdown complete")

if __name__ == '__main__':
    run_benchmarks()
