package com.tsm.mobile.viewModel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.tsm.mobile.data.SessionMetadata
import com.tsm.mobile.data.SessionMetadataDao
import com.tsm.mobile.network.NetworkManager
import com.tsm.mobile.proto.EncryptedSearchRequest
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import java.io.ByteArrayOutputStream
import java.io.ObjectOutputStream

class SessionViewModel(
    private val sessionMetadataDao: SessionMetadataDao,
    private val networkManager: NetworkManager
) : ViewModel() {

    private val _sessions = MutableStateFlow<List<SessionMetadata>>(emptyList())
    val sessions: StateFlow<List<SessionMetadata>> = _sessions

    private val _searchResults = MutableStateFlow<List<String>>(emptyList())
    val searchResults: StateFlow<List<String>> = _searchResults

    fun loadSessions() {
        // In a real app, this would be a call to the database
        // For now, we'll just use mock data
        _sessions.value = listOf(
            SessionMetadata("1", "2025-07-20", "test-user-1", "log1"),
            SessionMetadata("2", "2025-07-21", "test-user-2", "log2")
        )
    }

    fun searchSessions(searchTerm: String) {
        viewModelScope.launch {
            try {
                // In a real app, you would use the homomorphic search prototype
                // to generate the encrypted query. For now, we'll just send the
                // search term as is.
                val request = EncryptedSearchRequest.newBuilder()
                    .setEncryptedQuery(searchTerm)
                    .build()
                val response = networkManager.stub.encryptedSearch(request)
                _searchResults.value = response.sessionLocatorsList
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
}
