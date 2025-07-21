package com.tsm.mobile.viewModel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.tsm.mobile.data.SessionMetadata
import com.tsm.mobile.data.SessionMetadataDao
import com.tsm.mobile.network.NetworkManager
import com.tsm.mobile.proto.EncryptedSearchRequest
import com.tsm.mobile.proto.TSMServiceGrpc
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.io.ObjectOutputStream

/**
 * ViewModel responsible for managing session data and search functionality.
 * 
 * This ViewModel follows the MVVM pattern and serves as the bridge between
 * the UI layer (Compose screens) and the data layer (database and network).
 * It uses Kotlin Coroutines for asynchronous operations and StateFlow for
 * reactive UI updates.
 */
class SessionViewModel(
    private val sessionMetadataDao: SessionMetadataDao,
    private val networkManager: NetworkManager
) : ViewModel() {
    
    // StateFlow for the main session list
    // This holds all available sessions and updates the UI reactively
    private val _sessions = MutableStateFlow<List<SessionMetadata>>(emptyList())
    val sessions: StateFlow<List<SessionMetadata>> = _sessions
    
    // StateFlow for search results
    // Kept separate from main sessions to allow showing both simultaneously
    private val _searchResults = MutableStateFlow<List<String>>(emptyList())
    val searchResults: StateFlow<List<String>> = _searchResults
    
    // StateFlow for loading states
    // This helps the UI show loading indicators during network operations
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading
    
    // StateFlow for error messages
    // Allows the UI to display user-friendly error messages
    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage: StateFlow<String?> = _errorMessage
    
    init {
        // Load sessions when the ViewModel is created
        loadSessions()
    }
    
    /**
     * Loads all available sessions from the database.
     * 
     * In a production app, this would query the actual database.
     * Currently using mock data for prototype purposes.
     */
    fun loadSessions() {
        viewModelScope.launch {
            try {
                _isLoading.value = true
                
                // TODO: Replace with actual database query
                // val sessionsFromDb = withContext(Dispatchers.IO) {
                //     sessionMetadataDao.getAllSessions()
                // }
                
                // Mock data for prototype
                _sessions.value = listOf(
                    SessionMetadata("1", "2025-07-20", "test-user-1", "log1"),
                    SessionMetadata("2", "2025-07-21", "test-user-2", "log2"),
                    SessionMetadata("3", "2025-07-22", "test-user-3", "log3")
                )
                
                _errorMessage.value = null
            } catch (e: Exception) {
                _errorMessage.value = "Failed to load sessions: ${e.message}"
            } finally {
                _isLoading.value = false
            }
        }
    }
    
    /**
     * Performs a homomorphic encrypted search for sessions.
     * 
     * This method demonstrates how the client would:
     * 1. Generate an encrypted query using homomorphic encryption
     * 2. Send it to the server via gRPC
     * 3. Receive encrypted results that only this client can decrypt
     * 
     * @param searchTerm The term to search for (will be encrypted before sending)
     */
    fun searchSessions(searchTerm: String) {
        // Don't search if the term is empty
        if (searchTerm.isBlank()) {
            _searchResults.value = emptyList()
            return
        }
        
        viewModelScope.launch {
            try {
                _isLoading.value = true
                _errorMessage.value = null
                
                // Switch to IO dispatcher for network operations
                val results = withContext(Dispatchers.IO) {
                    // In a production implementation, this is where we would:
                    // 1. Generate the homomorphic encryption keys (or retrieve stored ones)
                    // 2. Encrypt the search term using the public key
                    // 3. Serialize the encrypted query
                    
                    // For the prototype, we're simulating the encrypted query
                    // In reality, this would use the HomomorphicSearchPrototype class
                    val encryptedQuery = simulateEncryptedQuery(searchTerm)
                    
                    // Build the gRPC request with the encrypted query
                    val request = EncryptedSearchRequest.newBuilder()
                        .setEncryptedQuery(encryptedQuery)
                        .build()
                    
                    // Send the request to the server and get the response
                    // The networkManager handles the gRPC channel and stub
                    val response = networkManager.stub.encryptedSearch(request)
                    
                    // Return the list of matching session locators
                    response.sessionLocatorsList
                }
                
                // Update the search results StateFlow
                _searchResults.value = results
                
            } catch (e: Exception) {
                // Handle different types of errors appropriately
                when (e) {
                    is io.grpc.StatusException -> {
                        _errorMessage.value = "Network error: ${e.status.description}"
                    }
                    else -> {
                        _errorMessage.value = "Search failed: ${e.message}"
                    }
                }
                
                // Clear results on error
                _searchResults.value = emptyList()
                
            } finally {
                _isLoading.value = false
            }
        }
    }
    
    /**
     * Simulates creating an encrypted query for the prototype.
     * 
     * In a production app, this would:
     * 1. Use the Paillier encryption library
     * 2. Encrypt the search term with the public key
     * 3. Serialize the encrypted object properly
     * 
     * @param searchTerm The term to encrypt
     * @return ByteString containing the "encrypted" query
     */
    private fun simulateEncryptedQuery(searchTerm: String): com.google.protobuf.ByteString {
        // For the prototype, we'll create a simple serialized object
        // In production, this would be a properly encrypted Paillier object
        
        val simulatedEncryptedData = mapOf(
            "pk" to "12345",  // Simulated public key
            "n" to searchTerm.hashCode().toString(),  // Simulated ciphertext
            "e" to "65537"  // Simulated exponent
        )
        
        // Serialize the map to bytes
        val byteStream = ByteArrayOutputStream()
        ObjectOutputStream(byteStream).use { objectStream ->
            objectStream.writeObject(simulatedEncryptedData)
        }
        
        return com.google.protobuf.ByteString.copyFrom(byteStream.toByteArray())
    }
    
    /**
     * Clears the current search results.
     * Called when the user clears the search bar or navigates away.
     */
    fun clearSearchResults() {
        _searchResults.value = emptyList()
    }
    
    /**
     * Clears any error messages.
     * Called when the user dismisses an error dialog or snackbar.
     */
    fun clearError() {
        _errorMessage.value = null
    }
    
    override fun onCleared() {
        super.onCleared()
        // Clean up resources if needed
        // The NetworkManager should handle closing the gRPC channel
    }
}