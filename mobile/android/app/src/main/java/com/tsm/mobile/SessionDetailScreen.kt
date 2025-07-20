package com.tsm.mobile.ui.screen

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.tsm.mobile.data.SessionMetadata

@Composable
fun SessionDetailScreen(sessionId: String) {
    // In a real application, you would fetch the session details from a ViewModel
    val session = SessionMetadata(
        id = sessionId,
        creationDate = "2025-07-20",
        associatedIdentity = "test-user",
        securityLogs = "No suspicious activity detected."
    )

    Column(modifier = Modifier.padding(16.dp)) {
        Text("Session Details", style = androidx.compose.material3.MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(16.dp))
        Text("ID: ${session.id}")
        Spacer(modifier = Modifier.height(8.dp))
        Text("Creation Date: ${session.creationDate}")
        Spacer(modifier = Modifier.height(8.dp))
        Text("Associated Identity: ${session.associatedIdentity}")
        Spacer(modifier = Modifier.height(8.dp))
        Text("Security Logs: ${session.securityLogs}")
    }
}
