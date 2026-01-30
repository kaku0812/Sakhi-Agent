package com.example.combinedflow

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.util.Log
import android.view.View
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.example.combinedflow.emergency.UberRideRequestManager
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationServices
class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "MainActivity"
        private const val OVERLAY_PERMISSION_REQUEST_CODE = 1234
    }

    private lateinit var uberRideRequestManager: UberRideRequestManager
    private lateinit var fusedLocationClient: FusedLocationProviderClient

    private fun updateStatusUI(isActive: Boolean) {
        val statusText = findViewById<TextView>(R.id.status_text)
        if (isActive) {
            statusText.text = "● Active"
            statusText.setTextColor(Color.parseColor("#4CAF50"))
        } else {
            statusText.text = "● Inactive"
            statusText.setTextColor(Color.parseColor("#FF6B6B"))
        }
    }
    private fun hasBackgroundLocationPermission(): Boolean {
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.Q ||
                checkSelfPermission(Manifest.permission.ACCESS_BACKGROUND_LOCATION) ==
                PackageManager.PERMISSION_GRANTED
    }

    private fun hasNotificationPermission(): Boolean {
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
                checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) ==
                PackageManager.PERMISSION_GRANTED
    }

    private val permissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { permissions ->

            val locationGranted =
                permissions[Manifest.permission.ACCESS_FINE_LOCATION] == true ||
                        permissions[Manifest.permission.ACCESS_COARSE_LOCATION] == true

            val smsGranted = permissions[Manifest.permission.SEND_SMS] == true
            val phoneGranted = permissions[Manifest.permission.READ_PHONE_STATE] == true
            val notifGranted = hasNotificationPermission()

            Log.d(TAG, "Permissions -> location=$locationGranted sms=$smsGranted phone=$phoneGranted notif=$notifGranted")

            if (locationGranted && smsGranted && phoneGranted && notifGranted && Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {

                if (!hasBackgroundLocationPermission()) {
                    openAppSettingsForBackgroundLocation()
                } else {
                    startSafetyService()
                }

            } else {
                Toast.makeText(this, "Required permissions not granted", Toast.LENGTH_LONG).show()
            }
        }


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Log.d("Main activity","On create of main activity")
        setContentView(R.layout.activity_main)
        
        // Initialize Uber ride request manager
        uberRideRequestManager = UberRideRequestManager(this)
        
        // Initialize location client for SOS button
        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)
    }

    /**
     * SOS Button Click - Sends SMS to trigger Kiro Agent for Uber ride booking
     */
    fun onSosButtonClick(view: View) {
        // Show confirmation dialog
        AlertDialog.Builder(this)
            .setTitle("🚨 Emergency Ride Request")
            .setMessage("This will send a request to book an Uber ride immediately.\n\nContinue?")
            .setPositiveButton("Yes, Book Ride") { _, _ ->
                sendUberRideRequest()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun sendUberRideRequest() {
        // Check SMS permission first
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.SEND_SMS) 
            != PackageManager.PERMISSION_GRANTED) {
            Toast.makeText(this, "SMS permission required for ride booking", Toast.LENGTH_SHORT).show()
            return
        }

        // Disable button temporarily to prevent double-tap
        val sosButton = findViewById<Button>(R.id.sos_button)
        sosButton.isEnabled = false
        sosButton.text = "🔄 Getting location..."

        // Get current location and then send ride request
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) 
            == PackageManager.PERMISSION_GRANTED) {
            
            fusedLocationClient.lastLocation.addOnSuccessListener { location ->
                sosButton.text = "🔄 Requesting ride..."
                
                if (location != null) {
                    // Send with location
                    Log.d(TAG, "Sending ride request with location: ${location.latitude}, ${location.longitude}")
                    uberRideRequestManager.requestEmergencyRideWithLocation(
                        location.latitude,
                        location.longitude,
                        createRideRequestCallback(sosButton)
                    )
                } else {
                    // Fallback: send without location
                    Log.d(TAG, "Location unavailable, sending basic ride request")
                    uberRideRequestManager.requestEmergencyRide(createRideRequestCallback(sosButton))
                }
            }.addOnFailureListener { e ->
                Log.e(TAG, "Failed to get location", e)
                sosButton.text = "🔄 Requesting ride..."
                // Fallback: send without location
                uberRideRequestManager.requestEmergencyRide(createRideRequestCallback(sosButton))
            }
        } else {
            // No location permission, send basic request
            sosButton.text = "🔄 Requesting ride..."
            uberRideRequestManager.requestEmergencyRide(createRideRequestCallback(sosButton))
        }
    }

    private fun createRideRequestCallback(sosButton: Button): UberRideRequestManager.RideRequestCallback {
        return object : UberRideRequestManager.RideRequestCallback {
            override fun onSmsSent() {
                runOnUiThread {
                    Toast.makeText(
                        this@MainActivity,
                        "✅ Ride request sent! Kiro agent will book your Uber.",
                        Toast.LENGTH_LONG
                    ).show()
                    sosButton.text = "✅ Request Sent"
                    
                    // Reset button after 5 seconds
                    sosButton.postDelayed({
                        sosButton.isEnabled = true
                        sosButton.text = "🚨 SOS - Book Emergency Ride"
                    }, 5000)
                }
            }

            override fun onSmsFailed(error: String) {
                runOnUiThread {
                    Toast.makeText(
                        this@MainActivity,
                        "❌ Failed to send request: $error",
                        Toast.LENGTH_LONG
                    ).show()
                    sosButton.isEnabled = true
                    sosButton.text = "🚨 SOS - Book Emergency Ride"
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()

        if (TrackingStore.isTrackingActive(this)) {
            Log.d(TAG, "Tracking already active")
            return
        }

        else if (!TrackingStore.isTrackingActive(this) &&
            hasBackgroundLocationPermission()
        ) {
            Log.d(TAG, "Resuming tracking after permissions")
            startSafetyService()
        }
    }

    fun startTracking(view: View) {
        if (TrackingStore.isTrackingActive(this)) {
            Log.d(TAG, "Tracking already active")
            return
        }

        val permissions = mutableListOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION,
            Manifest.permission.SEND_SMS,
            Manifest.permission.READ_PHONE_STATE
        )

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }

        permissionLauncher.launch(permissions.toTypedArray())
    }

    fun stopTracking(view: View) {
        stopService(Intent(this, SafetyService::class.java))
        stopService(Intent(this, FloatingSosService::class.java)) // Stop floating button too
        TrackingStore.setTracking(this, false)
        Toast.makeText(this, "Tracking stopped", Toast.LENGTH_SHORT).show()
        updateStatusUI(false)
    }

    private fun startSafetyService() {
        Log.d(TAG, "Starting SafetyService")

        TrackingStore.setTracking(this, true)

        val intent = Intent(this, SafetyService::class.java)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            ContextCompat.startForegroundService(this, intent)
        } else {
            startService(intent)
        }
        updateStatusUI(true)
        
        // Start floating SOS button (requires overlay permission)
        startFloatingSosButton()
    }
    
    private fun startFloatingSosButton() {
        // Check if we have overlay permission
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this)) {
            // Request overlay permission
            AlertDialog.Builder(this)
                .setTitle("Floating SOS Button")
                .setMessage("To show the SOS button on top of other apps, please grant 'Display over other apps' permission.")
                .setPositiveButton("Grant Permission") { _, _ ->
                    val intent = Intent(
                        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse("package:$packageName")
                    )
                    startActivityForResult(intent, OVERLAY_PERMISSION_REQUEST_CODE)
                }
                .setNegativeButton("Skip") { _, _ ->
                    Toast.makeText(this, "Floating button disabled. Use in-app SOS button instead.", Toast.LENGTH_LONG).show()
                }
                .show()
        } else {
            // Permission granted, start the floating service
            startFloatingService()
        }
    }
    
    private fun startFloatingService() {
        val floatingIntent = Intent(this, FloatingSosService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            ContextCompat.startForegroundService(this, floatingIntent)
        } else {
            startService(floatingIntent)
        }
        Log.d(TAG, "Floating SOS button started")
    }
    
    @Deprecated("Deprecated in Java")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == OVERLAY_PERMISSION_REQUEST_CODE) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && Settings.canDrawOverlays(this)) {
                startFloatingService()
                Toast.makeText(this, "✅ Floating SOS button enabled!", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, "Permission denied. Using in-app button only.", Toast.LENGTH_LONG).show()
            }
        }
    }
    
    private fun openAppSettingsForBackgroundLocation() {
        Toast.makeText(
            this,
            "Please allow background location for safety tracking",
            Toast.LENGTH_LONG
        ).show()

        val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
            data = Uri.fromParts("package", packageName, null)
        }
        startActivity(intent)
    }
}
