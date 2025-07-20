from phe import paillier

# Generate a Paillier keypair
public_key, private_key = paillier.generate_paillier_keypair()

# The numbers to be encrypted
a = 10
b = 20

# Encrypt the numbers
encrypted_a = public_key.encrypt(a)
encrypted_b = public_key.encrypt(b)

# Add the encrypted numbers
encrypted_sum = encrypted_a + encrypted_b

# Decrypt the result
decrypted_sum = private_key.decrypt(encrypted_sum)

# Print the results
print(f"The sum of {a} and {b} is {a+b}")
print(f"The decrypted sum is {decrypted_sum}")

# Verify the result
assert a + b == decrypted_sum
print("The homomorphic addition was successful!")
