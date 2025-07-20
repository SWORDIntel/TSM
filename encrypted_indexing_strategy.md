# Encrypted Indexing Strategy

This document outlines a strategy for creating a searchable encrypted index using the Paillier homomorphic encryption scheme.

## 1. Overview

The goal is to allow a client to search for a term in a database stored on an untrusted server, without revealing the search term to the server. We will use the additively homomorphic properties of the Paillier cryptosystem to achieve this.

## 2. Key Components

*   **Client:** The client has a Paillier keypair (public and private key). They are the only one with access to the private key.
*   **Server:** The server stores the encrypted database and performs the search operations. The server only has access to the public key.
*   **Encrypted Database:** A key-value store where the keys are plaintext identifiers and the values are the Paillier-encrypted representations of the corresponding keywords.

## 3. Indexing Process

1.  The client generates a Paillier keypair.
2.  For each keyword to be indexed, the client encrypts the keyword using their public key.
3.  The client sends the encrypted keywords to the server, along with their corresponding plaintext identifiers.
4.  The server stores this information in the encrypted database.

## 4. Search Process

1.  The client takes a search term and encrypts it using their public key.
2.  The client sends the encrypted search term to the server.
3.  The server iterates through each entry in the encrypted database. For each entry, it performs the following operation:
    ```
    encrypted_result = encrypted_database_entry - encrypted_search_term
    ```
    This is possible because the Paillier cryptosystem is additively homomorphic, and subtraction is a form of addition.
4.  The server sends all the `encrypted_result` values back to the client.

## 5. Result Interpretation

1.  The client receives the list of `encrypted_result` values from the server.
2.  The client decrypts each `encrypted_result` using their private key.
3.  If a decrypted result is equal to zero, it means that the corresponding keyword in the database matches the search term.
4.  The client can then identify the matching document(s) based on the plaintext identifiers associated with the matching keywords.

## 6. Security Considerations

*   **Information Leakage:** The server learns which documents match the query, even though it doesn't know what the query is. This is a known limitation of this approach. More advanced techniques like Private Information Retrieval (PIR) could be used to mitigate this, but they are out of scope for this prototype.
*   **Deterministic Encryption:** Since we are encrypting the same keyword with the same key, the ciphertext will always be the same. This can leak information. To mitigate this, we will use the randomized version of the Paillier encryption scheme provided by the `phe` library.
