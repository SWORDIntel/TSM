from phe import paillier

class HomomorphicSearchPrototype:
    """
    A prototype for homomorphic search on an encrypted database.
    """

    def __init__(self):
        """
        Initializes the prototype by generating a Paillier keypair.
        """
        self.public_key, self.private_key = paillier.generate_paillier_keypair()
        self.encrypted_database = {}

    def encrypt_keyword(self, keyword):
        """
        Encrypts a keyword using a simple XOR cipher.

        Args:
            keyword (str): The keyword to encrypt.

        Returns:
            bytes: The encrypted keyword.
        """
        key = b'secret_key'
        encrypted_keyword = bytearray()
        for i in range(len(keyword)):
            encrypted_keyword.append(keyword[i] ^ key[i % len(key)])
        return bytes(encrypted_keyword)

    def execute_search(self, encrypted_keywords, encrypted_inverted_index, operator):
        """
        Takes the encrypted keywords and inverted index, performs a lookup,
        and returns the session IDs of the matching items.

        Args:
            encrypted_keywords (list): A list of encrypted keywords.
            encrypted_inverted_index (dict): The encrypted inverted index.
            operator (str): The boolean operator to use ('AND' or 'OR').

        Returns:
            list: A list of session IDs of the matching items.
        """
        results = []
        for encrypted_keyword in encrypted_keywords:
            if encrypted_keyword in encrypted_inverted_index:
                results.append(set(encrypted_inverted_index[encrypted_keyword]))

        if not results:
            return []

        if operator == 'AND':
            return list(set.intersection(*results))
        elif operator == 'OR':
            return list(set.union(*results))

    def execute_and_search(self, encrypted_queries, encrypted_database):
        """
        Performs a homomorphic AND search.
        """
        for key, encrypted_value in encrypted_database.items():
            encrypted_diff_sum = self.public_key.encrypt(0)
            for encrypted_query in encrypted_queries:
                encrypted_diff_sum += encrypted_value - encrypted_query

            decrypted_diff = self.private_key.decrypt(encrypted_diff_sum)
            if decrypted_diff == 0:
                return key
        return None

    def execute_or_search(self, encrypted_queries, encrypted_database):
        """
        Performs a homomorphic OR search.
        """
        matching_keys = []
        for key, encrypted_value in encrypted_database.items():
            for encrypted_query in encrypted_queries:
                encrypted_diff = encrypted_value - encrypted_query
                decrypted_diff = self.private_key.decrypt(encrypted_diff)
                if decrypted_diff == 0:
                    matching_keys.append(key)
                    break
        return matching_keys

    def search_boolean(self, encrypted_queries, operator):
        """
        Performs a boolean search on the encrypted data.
        """
        if operator == "AND":
            return self.execute_and_search(encrypted_queries, self.encrypted_database)
        elif operator == "OR":
            return self.execute_or_search(encrypted_queries, self.encrypted_database)

if __name__ == '__main__':
    # Create an instance of the prototype
    prototype = HomomorphicSearchPrototype()

    # Create a sample database
    plain_database = {
        "alpha": [1, 2],
        "bravo": [2, 3],
        "charlie": [3, 4],
        "delta": [4, 5],
        "echo": [5, 6]
    }

    # Encrypt the database
    for key, values in plain_database.items():
        prototype.encrypted_database[key] = [prototype.public_key.encrypt(v) for v in values]

    # Generate encrypted queries
    search_terms = [3, 4]
    encrypted_queries = [prototype.public_key.encrypt(term) for term in search_terms]

    # Execute the search with AND operator
    matching_keys_and = prototype.search_boolean(encrypted_queries, 'AND')
    print(f"Found matches for search terms {search_terms} with AND operator at keys: {matching_keys_and}")
    assert "charlie" in matching_keys_and

    # Execute the search with OR operator
    matching_keys_or = prototype.search_boolean(encrypted_queries, 'OR')
    print(f"Found matches for search terms {search_terms} with OR operator at keys: {matching_keys_or}")
    assert "bravo" in matching_keys_or
    assert "charlie" in matching_keys_or
    assert "delta" in matching_keys_or
