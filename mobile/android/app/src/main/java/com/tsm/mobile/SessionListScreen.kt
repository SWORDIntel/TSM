package com.tsm.mobile.ui.screen

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.lifecycle.viewmodel.compose.viewModel
import com.tsm.mobile.ui.components.SearchBar
import com.tsm.mobile.viewModel.SessionViewModel

@Composable
fun SessionListScreen(
    sessionViewModel: SessionViewModel = viewModel()
) {
    val sessions by sessionViewModel.sessions.collectAsState()
    val searchResults by sessionViewModel.searchResults.collectAsState()

    Column {
        SearchBar(onSearch = { searchTerm ->
            sessionViewModel.searchSessions(searchTerm)
        })
        LazyColumn {
            items(sessions) { session ->
                Text(text = session.name)
            }
        }
        if (searchResults.isNotEmpty()) {
            Text("Search Results:")
            LazyColumn {
                items(searchResults) { result ->
                    Text(text = result)
                }
            }
        }
    }
}
