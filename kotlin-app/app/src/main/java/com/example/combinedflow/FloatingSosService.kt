package com.example.combinedflow

import android.Manifest
import android.annotation.SuppressLint
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.PixelFormat
import android.os.Build
import android.os.IBinder
import android.util.Log
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Toast
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import com.example.combinedflow.emergency.UberRideRequestManager
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationServices

/**
 * Floating SOS Button Service
 * Creates a persistent floating button that stays on screen even when app is closed
 */
class FloatingSosService : Service() {

    companion object {
        private const val TAG = "FloatingSosService"
        private const val NOTIF_CHANNEL_ID = "floating_sos_channel"
        private const val NOTIFICATION_ID = 2
    }

    private lateinit var windowManager: WindowManager
    private lateinit var floatingView: View
    private lateinit var uberRideRequestManager: UberRideRequestManager
    private lateinit var fusedLocationClient: FusedLocationProviderClient

    private var initialX = 0
    private var initialY = 0
    private var initialTouchX = 0f
    private var initialTouchY = 0f

    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "FloatingSosService created")

        uberRideRequestManager = UberRideRequestManager(this)
        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager

        createFloatingButton()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForeground(NOTIFICATION_ID, createNotification())
        return START_STICKY
    }

    @SuppressLint("ClickableViewAccessibility", "InflateParams")
    private fun createFloatingButton() {
        // Inflate the floating button layout
        floatingView = LayoutInflater.from(this).inflate(R.layout.floating_sos_button, null)

        // Set up window parameters
        val layoutParams = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            else
                WindowManager.LayoutParams.TYPE_PHONE,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = 0
            y = 300
        }

        // Add view to window
        windowManager.addView(floatingView, layoutParams)

        // Handle touch events for dragging and clicking
        floatingView.setOnTouchListener { view, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initialX = layoutParams.x
                    initialY = layoutParams.y
                    initialTouchX = event.rawX
                    initialTouchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    layoutParams.x = initialX + (event.rawX - initialTouchX).toInt()
                    layoutParams.y = initialY + (event.rawY - initialTouchY).toInt()
                    windowManager.updateViewLayout(floatingView, layoutParams)
                    true
                }
                MotionEvent.ACTION_UP -> {
                    // Check if it was a click (minimal movement)
                    val deltaX = event.rawX - initialTouchX
                    val deltaY = event.rawY - initialTouchY
                    if (Math.abs(deltaX) < 10 && Math.abs(deltaY) < 10) {
                        onSosButtonClicked()
                    }
                    true
                }
                else -> false
            }
        }
    }

    private fun onSosButtonClicked() {
        Log.d(TAG, "Floating SOS button clicked!")
        
        // Visual feedback
        Toast.makeText(this, "🚨 Requesting emergency ride...", Toast.LENGTH_SHORT).show()

        // Check SMS permission
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.SEND_SMS)
            != PackageManager.PERMISSION_GRANTED) {
            Toast.makeText(this, "SMS permission required", Toast.LENGTH_SHORT).show()
            return
        }

        // Get location and send request
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
            == PackageManager.PERMISSION_GRANTED) {
            
            fusedLocationClient.lastLocation.addOnSuccessListener { location ->
                if (location != null) {
                    Log.d(TAG, "Sending with location: ${location.latitude}, ${location.longitude}")
                    uberRideRequestManager.requestEmergencyRideWithLocation(
                        location.latitude,
                        location.longitude,
                        createCallback()
                    )
                } else {
                    uberRideRequestManager.requestEmergencyRide(createCallback())
                }
            }.addOnFailureListener {
                uberRideRequestManager.requestEmergencyRide(createCallback())
            }
        } else {
            uberRideRequestManager.requestEmergencyRide(createCallback())
        }
    }

    private fun createCallback(): UberRideRequestManager.RideRequestCallback {
        return object : UberRideRequestManager.RideRequestCallback {
            override fun onSmsSent() {
                android.os.Handler(mainLooper).post {
                    Toast.makeText(
                        this@FloatingSosService,
                        "✅ Ride request sent to Kiro agent!",
                        Toast.LENGTH_LONG
                    ).show()
                }
            }

            override fun onSmsFailed(error: String) {
                android.os.Handler(mainLooper).post {
                    Toast.makeText(
                        this@FloatingSosService,
                        "❌ Failed: $error",
                        Toast.LENGTH_LONG
                    ).show()
                }
            }
        }
    }

    private fun createNotification(): Notification {
        createNotificationChannel()

        val stopIntent = Intent(this, FloatingSosService::class.java).apply {
            action = "STOP_SERVICE"
        }
        val stopPendingIntent = PendingIntent.getService(
            this, 0, stopIntent,
            PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, NOTIF_CHANNEL_ID)
            .setContentTitle("SOS Button Active")
            .setContentText("Tap floating button for emergency ride")
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setOngoing(true)
            .addAction(R.drawable.ic_launcher_foreground, "Hide Button", stopPendingIntent)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                NOTIF_CHANNEL_ID,
                "Floating SOS Button",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Shows when floating SOS button is active"
            }
            getSystemService(NotificationManager::class.java)
                .createNotificationChannel(channel)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        if (::floatingView.isInitialized) {
            windowManager.removeView(floatingView)
        }
        Log.d(TAG, "FloatingSosService destroyed")
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
