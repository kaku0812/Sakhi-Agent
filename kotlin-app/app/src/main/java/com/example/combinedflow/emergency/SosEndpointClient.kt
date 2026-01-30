package com.example.combinedflow.emergency

import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.net.HttpURLConnection
import java.net.URL

/**
 * Simple HTTP client to call SOS endpoint
 * Kiro hook will listen to this endpoint and trigger the agent
 */
object SosEndpointClient {

    private const val TAG = "SosEndpointClient"
    
    // Deployed on Render - works everywhere!
    private const val ENDPOINT_URL = "https://serverforridebooking.onrender.com/book-ride"

    interface Callback {
        fun onSuccess(requestId: String)
        fun onError(error: String)
    }

    /**
     * Call the SOS endpoint with location coordinates
     */
    fun bookRide(latitude: Double, longitude: Double, userId: String = "sos_user", callback: Callback? = null) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val url = URL(ENDPOINT_URL)
                val connection = url.openConnection() as HttpURLConnection
                connection.requestMethod = "POST"
                connection.setRequestProperty("Content-Type", "application/json")
                connection.doOutput = true
                connection.connectTimeout = 10000
                connection.readTimeout = 10000

                val jsonBody = """{"latitude": $latitude, "longitude": $longitude, "user_id": "$userId"}"""
                connection.outputStream.use { it.write(jsonBody.toByteArray()) }

                val responseCode = connection.responseCode
                val response = connection.inputStream.bufferedReader().readText()
                
                Log.i(TAG, "SOS endpoint called! Response: $responseCode - $response")
                
                CoroutineScope(Dispatchers.Main).launch {
                    if (responseCode == 200) {
                        callback?.onSuccess(response)
                    } else {
                        callback?.onError("Server returned $responseCode")
                    }
                }

            } catch (e: Exception) {
                Log.e(TAG, "Failed to call SOS endpoint", e)
                CoroutineScope(Dispatchers.Main).launch {
                    callback?.onError(e.message ?: "Unknown error")
                }
            }
        }
    }
}
