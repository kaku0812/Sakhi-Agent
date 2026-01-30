package com.example.combinedflow.data

import android.content.Context
import android.util.Log
import androidx.work.*
import com.example.combinedflow.model.DeviceState
import com.example.combinedflow.worker.SyncWorker
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
class SnapshotManager(private val context: Context) {
    companion object {
        private const val TAG = "SnapshotManager"
    }

    private val db = AppDatabase.getDatabase(context)
    private val scope = CoroutineScope(Dispatchers.IO)

    fun captureSnapshot(deviceState: DeviceState) {
        Log.i(TAG, "Capturing snapshot: ${deviceState}")

        if (!deviceState.isValid()) {
            Log.w(TAG, "Skipping invalid snapshot")
            return
        }

        scope.launch {
            storeSnapshot(deviceState)
            scheduleSync()
        }
    }

    private suspend fun storeSnapshot(deviceState: DeviceState) {
        val snapshot = SnapshotEntity(
            timestamp = System.currentTimeMillis(),
            battery = deviceState.battery,
            networkAvailable = deviceState.isNetworkAvailable,
            lat = deviceState.lat,
            lng = deviceState.lng
        )

        db.snapshotDao().insert(snapshot)
        Log.d(TAG, "Snapshot saved")
    }

    private fun scheduleSync() {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()

        val workRequest = OneTimeWorkRequestBuilder<SyncWorker>()
            .setConstraints(constraints)
            .build()

        WorkManager.getInstance(context)
            .enqueueUniqueWork("snapshot_sync", ExistingWorkPolicy.KEEP, workRequest)
    }
}
