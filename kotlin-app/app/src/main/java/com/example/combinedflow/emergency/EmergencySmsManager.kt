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
import com.example.combinedflow.model.DeviceState
class EmergencySmsManager(private val context: Context) {

    companion object {
        private const val TAG = "EmergencySmsManager"
        //enter your phone number here
        private const val EMERGENCY_PHONE = ""
        private const val SMS_COOLDOWN = 10 * 60 * 1000L
    }

    private var lastSmsTime = 0L

    fun sendEmergencySmsIfNeeded(deviceState: DeviceState) {
        val now = System.currentTimeMillis()
        if (now - lastSmsTime < SMS_COOLDOWN) return

        if (!hasSmsPermissions()) {
            Log.e(TAG, "SMS permissions missing")
            return
        }

        lastSmsTime = now
        sendSms(buildMessage(deviceState))
    }

    private fun sendSms(message: String) {
        try {
            val smsManager = getSmsManager() ?: run {
                Log.e(TAG, "No valid SMS manager found")
                return
            }

            val parts = smsManager.divideMessage(message)
            val sentIntents = createPendingIntents(parts.size)
            val deliveryIntents = createPendingIntents(parts.size)

            smsManager.sendMultipartTextMessage(
                EMERGENCY_PHONE,
                null,
                parts,
                sentIntents,
                deliveryIntents
            )

            Log.i(TAG, "Emergency SMS sent")

        } catch (se: SecurityException) {
            Log.e(TAG, "SMS permission revoked at runtime", se)
        } catch (e: Exception) {
            Log.e(TAG, "SMS failed", e)
        }
    }

    private fun getSmsManager(): SmsManager? {
        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP_MR1) {
                val subscriptionManager =
                    context.getSystemService(Context.TELEPHONY_SUBSCRIPTION_SERVICE) as SubscriptionManager

                val activeSubscriptions = subscriptionManager.activeSubscriptionInfoList
                if (activeSubscriptions.isNullOrEmpty()) return null

                val dataSubId = SubscriptionManager.getDefaultDataSubscriptionId()
                val targetSim = activeSubscriptions.find {
                    it.subscriptionId == dataSubId
                } ?: activeSubscriptions.first()

                SmsManager.getSmsManagerForSubscriptionId(targetSim.subscriptionId)
            } else {
                SmsManager.getDefault()
            }
        } catch (se: SecurityException) {
            Log.e(TAG, "READ_PHONE_STATE permission missing", se)
            null
        }
    }


    private fun buildMessage(state: DeviceState): String = """                                                                                                                                      
        EMERGENCY ALERT                                                                                                                                                                             
                                                                                                                                                                                                    
        Battery: ${state.battery}%                                                                                                                                                                  
        Internet: ${if (state.isNetworkAvailable) "Available" else "Lost"}                                                                                                                          
        Location: ${state.getLocationString()}                                                                                                                                                      
                                                                                                                                                                                                    
        Please check on me.                                                                                                                                                                         
    """.trimIndent()

    private fun createPendingIntents(count: Int): ArrayList<PendingIntent> =
        ArrayList<PendingIntent>().apply {
            repeat(count) {
                add(PendingIntent.getBroadcast(
                    context, 0, Intent(), PendingIntent.FLAG_IMMUTABLE
                ))
            }
        }
    private fun hasSmsPermissions(): Boolean =
        context.checkSelfPermission(Manifest.permission.SEND_SMS) == PackageManager.PERMISSION_GRANTED &&
                context.checkSelfPermission(Manifest.permission.READ_PHONE_STATE) == PackageManager.PERMISSION_GRANTED
}

