import pickle
from homomorphic_search import HomomorphicSearchPrototype

class EncryptedIndexManager:
    def __init__(self, index_path='encrypted_index.pkl'):
        self.index_path = index_path
        self.search_prototype = HomomorphicSearchPrototype()
        self.encrypted_index = self._load_index()

    def _load_index(self):
        try:
            with open(self.index_path, 'rb') as f:
                index = pickle.load(f)
            with open('public_key.pkl', 'rb') as f_pk:
                self.search_prototype.public_key = pickle.load(f_pk)
            return index
        except FileNotFoundError:
            return {}

    def _save_index(self):
        with open(self.index_path, 'wb') as f:
            pickle.dump(self.encrypted_index, f)
        # Save the public key along with the index.
        with open('public_key.pkl', 'wb') as f_pk:
            pickle.dump(self.search_prototype.public_key, f_pk)

    def __init__(self, index_path='encrypted_inverted_index.pkl'):
        self.index_path = index_path
        self.search_prototype = HomomorphicSearchPrototype()
        self.encrypted_inverted_index = self._load_index()

    def update_index(self, session_id, keywords):
        for keyword in keywords:
            encrypted_keyword = self.search_prototype.encrypt_keyword(keyword)
            if encrypted_keyword not in self.encrypted_inverted_index:
                self.encrypted_inverted_index[encrypted_keyword] = []
            self.encrypted_inverted_index[encrypted_keyword].append(session_id)
        self._save_index()

    def get_inverted_index(self):
        return self.encrypted_inverted_index

    def get_search_prototype(self):
        return self.search_prototype
