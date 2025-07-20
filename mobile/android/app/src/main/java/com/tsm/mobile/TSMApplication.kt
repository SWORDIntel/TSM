package com.tsm.mobile

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class TSMApplication : Application() {
    override fun onCreate() {
        super.onCreate()
    }
}
