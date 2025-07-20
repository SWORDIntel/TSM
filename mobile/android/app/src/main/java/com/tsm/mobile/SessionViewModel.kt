package com.tsm.mobile.viewModel

import androidx.lifecycle.ViewModel
import com.tsm.mobile.data.SessionMetadata
import com.tsm.mobile.data.SessionMetadataDao
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

class SessionViewModel(private val sessionMetadataDao: SessionMetadataDao) : ViewModel() {

    private val _sessions = MutableStateFlow<List<SessionMetadata>>(emptyList())
    val sessions: StateFlow<List<SessionMetadata>> = _sessions

    fun loadSessions() {
        // In a real app, this would be a call to the database
        // For now, we'll just use mock data
        _sessions.value = listOf(
            SessionMetadata("1", "2025-07-20", "test-user-1", "log1"),
            SessionMetadata("2", "2025-07-21", "test-user-2", "log2")
        )
    }
}
