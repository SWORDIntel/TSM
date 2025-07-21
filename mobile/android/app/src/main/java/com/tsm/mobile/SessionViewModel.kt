package com.tsm.mobile.viewModel

import androidx.lifecycle.ViewModel
import com.tsm.mobile.data.SessionMetadata
import com.tsm.mobile.data.SessionMetadataDao
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import com.tsm.mobile.network.NetworkManager
import io.grpc.ManagedChannel
import io.grpc.ManagedChannelBuilder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.asExecutor
import com.tsm.mobile.proto.TSMServiceGrpc
import com.tsm.mobile.proto.EncryptedSearchRequest
import java.util.concurrent.Executors

class SessionViewModel(private val sessionMetadataDao: SessionMetadataDao) : ViewModel() {

    private val _sessions = MutableStateFlow<List<SessionMetadata>>(emptyList())
    val sessions: StateFlow<List<SessionMetadata>> = _sessions
    private val _searchResults = MutableStateFlow<List<String>>(emptyList())
    val searchResults: StateFlow<List<String>> = _searchResults

    private val channel: ManagedChannel = ManagedChannelBuilder.forAddress("10.0.2.2", 50051)
        .usePlaintext()
        .executor(Executors.newSingleThreadExecutor())
        .build()

    private val stub = TSMServiceGrpc.newBlockingStub(channel)


    fun loadSessions() {
        // In a real app, this would be a call to the database
        // For now, we'll just use mock data
        _sessions.value = listOf(
            SessionMetadata("1", "2025-07-20", "test-user-1", "log1"),
            SessionMetadata("2", "2025-07-21", "test-user-2", "log2")
        )
    }

    fun search(term: String) {
        // This is where the encrypted search would happen.
        // For now, we'll just filter the mock data.
        if (term.isBlank()) {
            _sessions.value = listOf(
                SessionMetadata("1", "2025-07-20", "test-user-1", "log1"),
                SessionMetadata("2", "2025-07-21", "test-user-2", "log2")
            )
        } else {
            _sessions.value = _sessions.value.filter {
                it.user.contains(term, ignoreCase = true) || it.logData.contains(term, ignoreCase = true)
            }
        }
    }
}
