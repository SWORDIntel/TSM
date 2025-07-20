package com.tsm.mobile.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query

@Dao
interface SessionMetadataDao {
    @Query("SELECT * FROM sessionmetadata")
    fun getAll(): List<SessionMetadata>

    @Insert
    fun insertAll(vararg sessions: SessionMetadata)
}
