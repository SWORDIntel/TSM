package com.tsm.mobile.data

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(entities = [SessionMetadata::class], version = 1)
abstract class TSMDatabase : RoomDatabase() {
    abstract fun sessionMetadataDao(): SessionMetadataDao
}
