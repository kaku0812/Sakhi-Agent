package com.example.combinedflow.network

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface ApiService {

    @POST("sync/snapshots")
    suspend fun uploadSnapshots(
        @Body payload: List<SnapshotPayload>
    ): Response<SyncResponse>
}