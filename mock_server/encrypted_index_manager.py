import pickle
from homomorphic_search import HomomorphicSearchPrototype

class EncryptedIndexManager:
    def __init__(self, index_path='encrypted_index.pkl', search_prototype=None):
        self.index_path = index_path
        self.inverted_index_path = 'encrypted_inverted_index.pkl'
        self._search_prototype_injected = search_prototype is not None
        
        if search_prototype:
            self.search_prototype = search_prototype
        else:
            self.search_prototype = HomomorphicSearchPrototype()
            
        # Load both types of indices
        self.encrypted_index = self._load_index()
        self.encrypted_inverted_index = self._load_inverted_index()
    
    def _load_index(self):
        """Load the numeric encrypted index"""
        if self._search_prototype_injected:
            try:
                with open(self.index_path, 'rb') as f:
                    index = pickle.load(f)
                return index
            except FileNotFoundError:
                return {}
        
        try:
            with open(self.index_path, 'rb') as f:
                index = pickle.load(f)
            with open('public_key.pkl', 'rb') as f_pk:
                self.search_prototype.public_key = pickle.load(f_pk)
            return index
        except FileNotFoundError:
            return {}
    
    def _load_inverted_index(self):
        """Load the keyword-based inverted index"""
        try:
            with open(self.inverted_index_path, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_index(self):
        """Save the numeric encrypted index"""
        with open(self.index_path, 'wb') as f:
            pickle.dump(self.encrypted_index, f)
        # Save the public key along with the index
        if not self._search_prototype_injected:
            with open('public_key.pkl', 'wb') as f_pk:
                pickle.dump(self.search_prototype.public_key, f_pk)
    
    def _save_inverted_index(self):
        """Save the keyword-based inverted index"""
        with open(self.inverted_index_path, 'wb') as f:
            pickle.dump(self.encrypted_inverted_index, f)
    
    def update_index(self, session_id, data):
        """Update numeric index - for backward compatibility"""
        # For numeric data, encrypt and store directly
        self.encrypted_index[session_id] = self.search_prototype.public_key.encrypt(data)
        self._save_index()
    
    def update_keyword_index(self, session_id, keywords):
        """Update keyword-based inverted index"""
        for keyword in keywords:
            encrypted_keyword = self.search_prototype.encrypt_keyword(keyword)
            if encrypted_keyword not in self.encrypted_inverted_index:
                self.encrypted_inverted_index[encrypted_keyword] = []
            if session_id not in self.encrypted_inverted_index[encrypted_keyword]:
                self.encrypted_inverted_index[encrypted_keyword].append(session_id)
        self._save_inverted_index()
    
    def get_index(self):
        """Get the numeric encrypted index"""
        return self.encrypted_index
    
    def get_inverted_index(self):
        """Get the keyword-based inverted index"""
        return self.encrypted_inverted_index
    
    def get_search_prototype(self):
        """Get the search prototype for external use"""
        return self.search_prototype
    
    def clear_indices(self):
        """Clear both indices - useful for testing"""
        self.encrypted_index = {}import pickle
from homomorphic_search import HomomorphicSearchPrototype

class EncryptedIndexManager:
    def __init__(self, index_path='encrypted_index.pkl', search_prototype=None):
        self.index_path = index_path
        self.inverted_index_path = 'encrypted_inverted_index.pkl'
        self._search_prototype_injected = search_prototype is not None
        
        if search_prototype:
            self.search_prototype = search_prototype
        else:
            self.search_prototype = HomomorphicSearchPrototype()
            
        # Load both types of indices
        self.encrypted_index = self._load_index()
        self.encrypted_inverted_index = self._load_inverted_index()
    
    def _load_index(self):
        """Load the numeric encrypted index"""
        if self._search_prototype_injected:
            try:
                with open(self.index_path, 'rb') as f:
                    index = pickle.load(f)
                return index
            except FileNotFoundError:
                return {}
        
        try:
            with open(self.index_path, 'rb') as f:
                index = pickle.load(f)
            with open('public_key.pkl', 'rb') as f_pk:
                self.search_prototype.public_key = pickle.load(f_pk)
            return index
        except FileNotFoundError:
            return {}
    
    def _load_inverted_index(self):
        """Load the keyword-based inverted index"""
        try:
            with open(self.inverted_index_path, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_index(self):
        """Save the numeric encrypted index"""
        with open(self.index_path, 'wb') as f:
            pickle.dump(self.encrypted_index, f)
        # Save the public key along with the index
        if not self._search_prototype_injected:
            with open('public_key.pkl', 'wb') as f_pk:
                pickle.dump(self.search_prototype.public_key, f_pk)
    
    def _save_inverted_index(self):
        """Save the keyword-based inverted index"""
        with open(self.inverted_index_path, 'wb') as f:
            pickle.dump(self.encrypted_inverted_index, f)
    
    def update_index(self, session_id, data):
        """Update numeric index - for backward compatibility"""
        # For numeric data, encrypt and store directly
        self.encrypted_index[session_id] = self.search_prototype.public_key.encrypt(data)
        self._save_index()
    
    def update_keyword_index(self, session_id, keywords):
        """Update keyword-based inverted index"""
        for keyword in keywords:
            encrypted_keyword = self.search_prototype.encrypt_keyword(keyword)
            if encrypted_keyword not in self.encrypted_inverted_index:
                self.encrypted_inverted_index[encrypted_keyword] = []
            if session_id not in self.encrypted_inverted_index[encrypted_keyword]:
                self.encrypted_inverted_index[encrypted_keyword].append(session_id)
        self._save_inverted_index()
    
    def get_index(self):
        """Get the numeric encrypted index"""
        return self.encrypted_index
    
    def get_inverted_index(self):
        """Get the keyword-based inverted index"""
        return self.encrypted_inverted_index
    
    def get_search_prototype(self):
        """Get the search prototype for external use"""
        return self.search_prototype
    
    def clear_indices(self):
        """Clear both indices - useful for testing"""
        self.encrypted_index = {}
        self.encrypted_inverted_index = {}
        self._save_index()
        self._save_inverted_index()
        self.encrypted_inverted_index = {}
        self._save_index()
        self._save_inverted_index()