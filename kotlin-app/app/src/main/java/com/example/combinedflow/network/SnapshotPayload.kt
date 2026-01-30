package com.example.combinedflow.network
data class SnapshotPayload(
    val local_id: Long,
    val timestamp: Long,
    val battery: Int,
    val network: Boolean,
    val lat: Double?,
    val lng: Double?
)
