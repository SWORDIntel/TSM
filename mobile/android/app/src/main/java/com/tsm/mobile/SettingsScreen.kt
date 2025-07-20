package com.tsm.mobile.ui.screen

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun SettingsScreen() {
    val (notificationsEnabled, setNotificationsEnabled) = remember { mutableStateOf(true) }
    val (darkModeEnabled, setDarkModeEnabled) = remember { mutableStateOf(false) }
    val (showConfirmationDialog, setShowConfirmationDialog) = remember { mutableStateOf(false) }

    Column(modifier = Modifier.padding(16.dp)) {
        Text("Settings", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(16.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("Enable Notifications")
            Spacer(modifier = Modifier.weight(1f))
            Switch(
                checked = notificationsEnabled,
                onCheckedChange = setNotificationsEnabled
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("Dark Mode")
            Spacer(modifier = Modifier.weight(1f))
            Switch(
                checked = darkModeEnabled,
                onCheckedChange = setDarkModeEnabled
            )
        }

        Spacer(modifier = Modifier.height(32.dp))

        Button(onClick = { setShowConfirmationDialog(true) }) {
            Text("Remote Wipe")
        }
    }

    if (showConfirmationDialog) {
        ConfirmationDialog(
            onConfirm = {
                // Handle remote wipe logic here
                setShowConfirmationDialog(false)
            },
            onDismiss = { setShowConfirmationDialog(false) }
        )
    }
}
