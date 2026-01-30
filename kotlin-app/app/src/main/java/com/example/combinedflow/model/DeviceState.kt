package com.example.combinedflow.model

data class DeviceState(
    var battery: Int = -1,
    var isNetworkAvailable: Boolean = true,
    var lat: Double? = null,
    var lng: Double? = null
) {
    fun isValid(): Boolean = battery != -1 && lat != null && lng != null

    fun getLocationString(): String =
        if (lat != null && lng != null) "Lat: $lat, Lng: $lng"
        else "Location unavailable"
}
