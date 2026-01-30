package com.example.combinedflow.emergency

import android.Manifest
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.telephony.SmsManager
import android.telephony.SubscriptionManager
import android.util.Log
import androidx.core.content.ContextCompat

/**
 * Handles sending SMS AND calling Render API to trigger Uber ride booking
 */
class UberRideRequestManager(private val context: Context) {

    companion object {
        private const val TAG = "UberRideRequestManager"
        // Enter your Kiro agent phone number here (for SMS-based ride requests)
        private const val KIRO_AGENT_PHONE = ""
        private const val RIDE_REQUEST_MESSAGE = "book a ride"
    }

    interface RideRequestCallback {
        fun onSmsSent()
        fun onSmsFailed(error: String)
    }

    fun requestEmergencyRide(callback: RideRequestCallback? = null) {
        // 1. Send SMS
        sendSms(RIDE_REQUEST_MESSAGE, callback)
        
        // 2. Call Render API
        SosEndpointClient.bookRide(0.0, 0.0, "sos_user")
    }

    /**
     * Send ride request with location details - triggers BOTH SMS and API
     */
    fun requestEmergencyRideWithLocation(
        latitude: Double,
        longitude: Double,
        callback: RideRequestCallback? = null
    ) {
        val message = "book a ride from $latitude,$longitude"
        
        // 1. Send SMS
        sendSms(message, callback)
        
        // 2. Call Render API with location
        SosEndpointClient.bookRide(latitude, longitude, "sos_user", object : SosEndpointClient.Callback {
            override fun onSuccess(requestId: String) {
                Log.i(TAG, "API call successful: $requestId")
            }
            override fun onError(error: String) {
                Log.e(TAG, "API call failed: $error")
            }
        })
    }

    private fun sendSms(message: String, callback: RideRequestCallback?) {
        if (!hasSmsPermission()) {
            Log.e(TAG, "SMS permission not granted")
            callback?.onSmsFailed("SMS permission not granted")
            return
        }

        try {
            val smsManager = getSmsManager() ?: run {
                callback?.onSmsFailed("SMS service unavailable")
                return
            }

            val sentIntent = PendingIntent.getBroadcast(
                context,
                0,
                Intent("SMS_SENT_UBER"),
                PendingIntent.FLAG_IMMUTABLE
            )

            smsManager.sendTextMessage(
                KIRO_AGENT_PHONE,
                null,
                message,
                sentIntent,
                null
            )

            Log.i(TAG, "SMS sent + API called: '$message'")
            callback?.onSmsSent()

        } catch (e: Exception) {
            Log.e(TAG, "Failed to send SMS", e)
            callback?.onSmsFailed(e.message ?: "Unknown error")
        }
    }

    private fun hasSmsPermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.SEND_SMS
        ) == PackageManager.PERMISSION_GRANTED
    }

    private fun getSmsManager(): SmsManager? {
        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP_MR1) {
                val subscriptionManager =
                    context.getSystemService(Context.TELEPHONY_SUBSCRIPTION_SERVICE) as SubscriptionManager

                val activeSubscriptions = subscriptionManager.activeSubscriptionInfoList
                if (activeSubscriptions.isNullOrEmpty()) return SmsManager.getDefault()

                // Use getDefaultDataSubscriptionId like EmergencySmsManager (which works)
                val dataSubId = SubscriptionManager.getDefaultDataSubscriptionId()
                val targetSim = activeSubscriptions.find {
                    it.subscriptionId == dataSubId
                } ?: activeSubscriptions.first()

                SmsManager.getSmsManagerForSubscriptionId(targetSim.subscriptionId)
            } else {
                SmsManager.getDefault()
            }
        } catch (se: SecurityException) {
            Log.e(TAG, "READ_PHONE_STATE permission missing, using default", se)
            SmsManager.getDefault()
        } catch (e: Exception) {
            Log.e(TAG, "Error getting SmsManager, using default", e)
            SmsManager.getDefault()
        }
    }
}
