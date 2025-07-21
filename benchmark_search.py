import time
import memory_profiler
from homomorphic_search import HomomorphicSearchPrototype

def benchmark_search(num_documents, prototype, benchmark_memory=True):
    """
    Benchmarks the homomorphic search feature.
    """
    print(f"Benchmarking with {num_documents} documents...")

    # Create a sample database
    plain_database = {f"document_{i}": i for i in range(num_documents)}

    # Encrypt the database
    encrypted_database = prototype.generate_encrypted_database(plain_database)

    # Generate an encrypted query
    search_term = num_documents // 2
    encrypted_query = prototype.generate_encrypted_query(search_term)

    # Measure execution time
    def search():
        prototype.execute_search(encrypted_query, encrypted_database)

    start_time = time.time()
    search()
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.4f} seconds")

    # Measure memory usage
    if benchmark_memory:
        mem_usage = memory_profiler.memory_usage(
            (search),
            interval=0.1,
            timeout=1
        )
        print(f"Peak memory usage: {max(mem_usage):.2f} MB")
    print("-" * 20)

if __name__ == '__main__':
    prototype = HomomorphicSearchPrototype()
    for num_docs in [100, 1000]:
        benchmark_search(num_docs, prototype)
    benchmark_search(5000, prototype, benchmark_memory=False)
