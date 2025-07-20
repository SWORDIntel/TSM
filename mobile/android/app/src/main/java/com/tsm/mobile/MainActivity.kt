package com.tsm.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import com.tsm.mobile.ui.theme.TSMTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            TSMTheme {
                Surface(color = MaterialTheme.colorScheme.background) {
                    // Main navigation will be set up here
                }
            }
        }
    }
}
