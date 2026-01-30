package com.example.combinedflow.monitoring

import android.Manifest
import android.annotation.SuppressLint
import android.content.*
import android.content.pm.PackageManager
import android.net.*
import android.os.*
import android.util.Log
import com.google.android.gms.location.*
import com.example.combinedflow.model.DeviceState

class DeviceMonitor(
    private val context: Context,
    private val deviceState: DeviceState,
    private val onEmergency: () -> Unit
) {

    companion object {
        private const val TAG = "DeviceMonitor"
        private const val CRITICAL_BATTERY = 10
    }

    private lateinit var fusedClient: FusedLocationProviderClient
    private lateinit var connectivityManager: ConnectivityManager
    private lateinit var networkCallback: ConnectivityManager.NetworkCallback
    private lateinit var batteryReceiver: BroadcastReceiver
    private lateinit var locationCallback: LocationCallback

    private var lastNetworkState = true

    fun startMonitoring() {
        setupLocationTracking()
        setupNetworkMonitoring()
        setupBatteryMonitoring()
    }

    fun stopMonitoring() {
        if (::fusedClient.isInitialized && ::locationCallback.isInitialized) {
            fusedClient.removeLocationUpdates(locationCallback)
        }

        if (::batteryReceiver.isInitialized) {
            context.unregisterReceiver(batteryReceiver)
        }

        if (::networkCallback.isInitialized) {
            connectivityManager.unregisterNetworkCallback(networkCallback)
        }
    }

    private fun setupLocationTracking() {
        if (!hasLocationPermission()) return

        fusedClient = LocationServices.getFusedLocationProviderClient(context)

        locationCallback = object : LocationCallback() {
            override fun onLocationResult(result: LocationResult) {
                result.lastLocation?.let { location ->
                    deviceState.lat = location.latitude
                    deviceState.lng = location.longitude
                }
            }
        }

        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 10_000L)
            .setMinUpdateIntervalMillis(5_000L)
            .build()

        @SuppressLint("MissingPermission")
        fusedClient.requestLocationUpdates(request, locationCallback, Looper.getMainLooper())
    }

    private fun setupNetworkMonitoring() {
        connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager

        networkCallback = object : ConnectivityManager.NetworkCallback() {
            override fun onCapabilitiesChanged(network: Network, caps: NetworkCapabilities) {
                val isAvailable = caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
                        caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
                handleNetworkChange(isAvailable)
            }

            override fun onLost(network: Network) {
                handleNetworkChange(false)
            }
        }

        connectivityManager.registerDefaultNetworkCallback(networkCallback)
    }

    private fun handleNetworkChange(isAvailable: Boolean) {
        val wasAvailable = lastNetworkState
        deviceState.isNetworkAvailable = isAvailable
        lastNetworkState = isAvailable

        if (wasAvailable && !isAvailable) {
            Log.w(TAG, "Network lost")
            onEmergency()
        }
    }

    private fun setupBatteryMonitoring() {
        batteryReceiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context?, intent: Intent?) {
                val batteryLevel = getBatteryLevel(intent)
                deviceState.battery = batteryLevel

                if (batteryLevel in 1..CRITICAL_BATTERY) {
                    Log.w(TAG, "Critical battery: $batteryLevel%")
                    onEmergency()
                }
            }
        }

        context.registerReceiver(batteryReceiver, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
    }

    private fun getBatteryLevel(intent: Intent?): Int {
        intent ?: return -1
        val level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
        val scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
        return if (level >= 0 && scale > 0) (level * 100) / scale else -1
    }

    private fun hasLocationPermission(): Boolean =
        context.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED ||
                context.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED
}
