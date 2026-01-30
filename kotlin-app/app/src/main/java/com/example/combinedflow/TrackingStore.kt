package com.example.combinedflow

import android.content.Context
import android.content.SharedPreferences

object TrackingStore {
    private const val PREFS_NAME = "tracking"
    private const val KEY_ACTIVE = "active"

    private fun getPrefs(context: Context): SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun setTracking(context: Context, isActive: Boolean) {
        getPrefs(context).edit()
            .putBoolean(KEY_ACTIVE, isActive)
            .apply()
    }

    fun isTrackingActive(context: Context): Boolean =
        getPrefs(context).getBoolean(KEY_ACTIVE, false)
}
