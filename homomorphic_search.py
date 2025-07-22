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

    def generate_encrypted_database(self, plain_database):
        """
        Creates a simple dictionary where keys are plaintext words and values
        are their homomorphically encrypted representations.

        Args:
            plain_database (dict): A dictionary with plaintext keys and values.

        Returns:
            dict: A dictionary with the same keys, but with encrypted values.
        """
        encrypted_database = {}
        for key, value in plain_database.items():
            encrypted_database[key] = self.public_key.encrypt(value)
        return encrypted_database

    def generate_encrypted_query(self, term):
        """
        Takes a plaintext search term and returns its encrypted form.

        Args:
            term (int): The plaintext search term.

        Returns:
            Paillier.EncryptedNumber: The encrypted search term.
        """
        return self.public_key.encrypt(term)

    def execute_search(self, encrypted_queries, encrypted_database, operator):
        """
        Takes the encrypted queries and database, performs a homomorphic
        comparison, and returns the plaintext keys of the matching items.

        Args:
            encrypted_queries (list): A list of encrypted search terms.
            encrypted_database (dict): The encrypted database.
            operator (str): The boolean operator to use ('AND' or 'OR').

        Returns:
            list: A list of plaintext keys of the matching items.
        """
        matching_keys = []
        for key, encrypted_value in encrypted_database.items():
            matches = []
            for encrypted_query in encrypted_queries:
                encrypted_diff = encrypted_value - encrypted_query
                decrypted_diff = self.private_key.decrypt(encrypted_diff)
                matches.append(decrypted_diff == 0)

            if operator == 'AND' and all(matches):
                matching_keys.append(key)
            elif operator == 'OR' and any(matches):
                matching_keys.append(key)
        return matching_keys

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
    encrypted_database = {}
    for key, values in plain_database.items():
        encrypted_database[key] = [prototype.public_key.encrypt(v) for v in values]

    # Generate encrypted queries
    search_terms = [3, 4]
    encrypted_queries = [prototype.generate_encrypted_query(term) for term in search_terms]

    # Execute the search with AND operator
    matching_keys_and = prototype.execute_search(encrypted_queries, encrypted_database, 'AND')
    print(f"Found matches for search terms {search_terms} with AND operator at keys: {matching_keys_and}")
    assert "charlie" in matching_keys_and

    # Execute the search with OR operator
    matching_keys_or = prototype.execute_search(encrypted_queries, encrypted_database, 'OR')
    print(f"Found matches for search terms {search_terms} with OR operator at keys: {matching_keys_or}")
    assert "bravo" in matching_keys_or
    assert "charlie" in matching_keys_or
    assert "delta" in matching_keys_or
