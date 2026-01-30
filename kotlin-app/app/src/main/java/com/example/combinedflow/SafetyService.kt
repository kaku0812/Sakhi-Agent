package com.example.combinedflow

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import androidx.core.app.NotificationCompat
import com.example.combinedflow.data.SnapshotManager
import com.example.combinedflow.emergency.EmergencySmsManager
import com.example.combinedflow.model.DeviceState
import com.example.combinedflow.monitoring.DeviceMonitor

class SafetyService : Service() {

    companion object {
        private const val TAG = "SafetyService"
        private const val NOTIF_CHANNEL_ID = "safety_channel"
        private const val NOTIFICATION_ID = 1
        private const val SNAPSHOT_INTERVAL = 30_000L
    }

    private val deviceState = DeviceState()
    private lateinit var deviceMonitor: DeviceMonitor
    private lateinit var emergencySmsManager: EmergencySmsManager
    private lateinit var snapshotManager: SnapshotManager

    private val handler = Handler(Looper.getMainLooper())

    private val snapshotRunnable = object : Runnable {
        override fun run() {
            snapshotManager.captureSnapshot(deviceState)
            handler.postDelayed(this, SNAPSHOT_INTERVAL)
        }
    }

    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "Service created")

        emergencySmsManager = EmergencySmsManager(this)
        snapshotManager = SnapshotManager(this)
        deviceMonitor = DeviceMonitor(this, deviceState) {
            emergencySmsManager.sendEmergencySmsIfNeeded(deviceState)
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {

        startForeground(NOTIFICATION_ID, createNotification())

        deviceMonitor.startMonitoring()
        handler.post(snapshotRunnable)

        return START_STICKY

    }

    override fun onDestroy() {
        super.onDestroy()
        handler.removeCallbacks(snapshotRunnable)
        deviceMonitor.stopMonitoring()
        Log.d(TAG, "Service destroyed")
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createNotification(): Notification {
        createNotificationChannel()

        return NotificationCompat.Builder(this, NOTIF_CHANNEL_ID)
            .setContentTitle("Safety Tracking Active")
            .setContentText("Monitoring battery, network & location")
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setOngoing(true)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .setForegroundServiceBehavior(
                NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE
            )
            .build()
    }
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                NOTIF_CHANNEL_ID,
                "Safety Tracking",
                NotificationManager.IMPORTANCE_DEFAULT
            )
            getSystemService(NotificationManager::class.java)
                .createNotificationChannel(channel)
        }
    }
}
