package com.example.combinedflow.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query

@Dao
interface SnapshotDao {
    @Insert
    suspend fun insert(snapshot: SnapshotEntity)

    @Query("SELECT * FROM snapshots WHERE synced = 0 ORDER BY timestamp ASC")
    suspend fun getUnsynced(): List<SnapshotEntity>

    @Query("UPDATE snapshots SET synced = 1 WHERE localId IN (:ids)")
    suspend fun markSynced(ids: List<Long>)
}
