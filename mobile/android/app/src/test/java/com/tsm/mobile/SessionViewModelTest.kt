package com.tsm.mobile

import com.tsm.mobile.data.SessionMetadata
import com.tsm.mobile.data.SessionMetadataDao
import com.tsm.mobile.viewModel.SessionViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.mockito.kotlin.mock
import org.mockito.kotlin.whenever

@ExperimentalCoroutinesApi
class SessionViewModelTest {

    private lateinit var viewModel: SessionViewModel
    private lateinit var sessionDao: SessionMetadataDao
    private val testDispatcher = StandardTestDispatcher()

    @BeforeEach
    fun setup() {
        Dispatchers.setMain(testDispatcher)
        sessionDao = mock()
        viewModel = SessionViewModel(sessionDao)
    }

    @AfterEach
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `loadSessions updates sessions state flow`() = runTest {
        val mockSessions = listOf(
            SessionMetadata("1", "2025-07-20", "test-user-1", "log1"),
            SessionMetadata("2", "2025-07-21", "test-user-2", "log2")
        )
        whenever(sessionDao.getAll()).thenReturn(mockSessions)

        viewModel.loadSessions()
        testDispatcher.scheduler.advanceUntilIdle() // Advance the dispatcher to execute the coroutine
        val sessions = viewModel.sessions.first()

        assertEquals(mockSessions, sessions)
    }
}
