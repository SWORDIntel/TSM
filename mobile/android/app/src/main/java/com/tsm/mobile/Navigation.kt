package com.tsm.mobile.ui

import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.tsm.mobile.ui.screen.SessionListScreen
import com.tsm.mobile.ui.screen.SettingsScreen

@Composable
fun AppNavigation() {
    val navController = rememberNavController()
    NavHost(navController = navController, startDestination = "session_list") {
        composable("session_list") { SessionListScreen() }
        composable("settings") { SettingsScreen() }
    }
}
