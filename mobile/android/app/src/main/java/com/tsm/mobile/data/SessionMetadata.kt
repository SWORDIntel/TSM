package com.tsm.mobile.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity
data class SessionMetadata(
    @PrimaryKey val id: String,
    val name: String,
    val creationDate: Long,
    val lastUsedDate: Long,
    val size: Long,
    val isEncrypted: Boolean
)
