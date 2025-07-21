package com.tsm.mobile.ui.screen

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Divider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.tsm.mobile.ui.components.SearchBar
import com.tsm.mobile.viewModel.SessionViewModel

@Composable
fun SessionListScreen(
    sessionViewModel: SessionViewModel = viewModel()
) {
    // Collect state from the ViewModel
    // This ensures our UI recomposes when the data changes
    val sessions by sessionViewModel.sessions.collectAsState()
    val searchResults by sessionViewModel.searchResults.collectAsState()
    
    // Main container that fills the entire screen
    Column(
        modifier = Modifier.fillMaxSize()
    ) {
        // Search functionality at the top of the screen
        // This component handles user input and triggers searches
        SearchBar(
            onSearch = { searchTerm ->
                // Call the ViewModel method to perform the search
                // This keeps our UI layer separate from business logic
                sessionViewModel.searchSessions(searchTerm)
            }
        )
        
        // Main session list
        // This shows all available sessions when not searching
        LazyColumn(
            modifier = Modifier.weight(1f) // Takes remaining space
        ) {
            items(sessions) { session ->
                // Display each session with its name
                // Using session.name provides more user-friendly display than session.id
                Text(
                    text = session.name,
                    modifier = Modifier.padding(
                        horizontal = 16.dp,
                        vertical = 8.dp
                    )
                )
            }
        }
        
        // Search results section
        // Only displayed when we have search results to show
        if (searchResults.isNotEmpty()) {
            // Visual separator between regular list and search results
            Divider()
            
            // Header for search results section
            Text(
                text = "Search Results:",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(
                    start = 16.dp,
                    top = 8.dp,
                    bottom = 4.dp
                )
            )
            
            // Search results list
            // Using a separate LazyColumn allows independent scrolling
            LazyColumn(
                modifier = Modifier.weight(0.5f) // Takes half the remaining space
            ) {
                items(searchResults) { result ->
                    Text(
                        text = result,
                        modifier = Modifier.padding(
                            horizontal = 16.dp,
                            vertical = 4.dp
                        )
                    )
                }
            }
        }
    }
}