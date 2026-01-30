package com.example.combinedflow.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "snapshots")
data class SnapshotEntity(
    @PrimaryKey(autoGenerate = true)
    val localId: Long = 0L,

    val timestamp: Long,

    val battery: Int,

    val networkAvailable: Boolean,

    val lat: Double?,
    val lng: Double?,

    val synced: Boolean = false
)
