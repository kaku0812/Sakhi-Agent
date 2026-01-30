package com.example.combinedflow.worker

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters

import com.example.combinedflow.network.SnapshotPayload
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import android.util.Log
import com.example.combinedflow.data.AppDatabase
import com.example.combinedflow.network.Api


class SyncWorker(
    ctx: Context,
    params: WorkerParameters
) : CoroutineWorker(ctx, params) {

    companion object {
        private const val TAG = "SyncWorker"
    }

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {

        try {
            val dao = AppDatabase.getDatabase(applicationContext).snapshotDao()
            val unsynced = dao.getUnsynced()

            if (unsynced.isEmpty()) {
                Log.d(TAG, "No unsynced snapshots found")
                return@withContext Result.success()
            }

            Log.d(TAG, "Found ${unsynced.size} unsynced snapshots")

            val payload = unsynced.map {
                SnapshotPayload(
                    local_id = it.localId,
                    timestamp = it.timestamp,
                    battery = it.battery,
                    network = it.networkAvailable,
                    lat = it.lat,
                    lng = it.lng
                )
            }

            val response = Api.uploadSnapshots(payload)

            if (response.isSuccessful && response.body() != null) {
                dao.markSynced(response.body()!!.acked_ids)
                Log.d(TAG, "Successfully synced snapshots")
                Result.success()
            } else {
                Log.e(TAG, "Server error while syncing")
                Result.retry()
            }

        } catch (e: Exception) {
            Log.e(TAG, "Sync failed", e)
            Result.retry()
        }
    }
}
