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

    def execute_search(self, encrypted_query, encrypted_database):
        """
        Takes the encrypted query and database, performs a homomorphic
        comparison (e.g., encrypted subtraction, where a result of encrypted
        zero indicates a match), and returns the plaintext key of the
        matching item.

        Args:
            encrypted_query (Paillier.EncryptedNumber): The encrypted search term.
            encrypted_database (dict): The encrypted database.

        Returns:
            str: The plaintext key of the matching item, or None if no match is found.
        """
        for key, encrypted_value in encrypted_database.items():
            # Homomorphically subtract the query from the database value
            encrypted_diff = encrypted_value - encrypted_query

            # Decrypt the difference
            decrypted_diff = self.private_key.decrypt(encrypted_diff)

            # If the difference is zero, we have a match
            if decrypted_diff == 0:
                return key
        return None

if __name__ == '__main__':
    # Create an instance of the prototype
    prototype = HomomorphicSearchPrototype()

    # Create a sample database
    plain_database = {
        "alpha": 1,
        "bravo": 2,
        "charlie": 3,
        "delta": 4,
        "echo": 5
    }

    # Encrypt the database
    encrypted_database = prototype.generate_encrypted_database(plain_database)

    # Generate an encrypted query
    search_term = 3
    encrypted_query = prototype.generate_encrypted_query(search_term)

    # Execute the search
    matching_key = prototype.execute_search(encrypted_query, encrypted_database)

    # Print the result
    if matching_key:
        print(f"Found a match for search term {search_term} at key: {matching_key}")
    else:
        print(f"No match found for search term {search_term}")

    # Verify that the correct key was found
    assert matching_key == "charlie"
