package com.tsm.mobile.ui.screen

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import com.tsm.mobile.viewModel.SessionViewModel

@Composable
fun SessionListScreen(sessionViewModel: SessionViewModel = viewModel()) {
    val sessions by sessionViewModel.sessions.collectAsState()

    Column(modifier = Modifier.fillMaxSize()) {
        SearchBar(onSearch = { query -> sessionViewModel.search(query) })
        LazyColumn {
            items(sessions) { session ->
                Text("Session: ${session.id}")
            }
        }
    }
}
