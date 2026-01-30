package com.example.combinedflow.network

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object Api {
    // Render-hosted backend (permanent URL)
    const val BASE_URL: String = "https://sakhi-location-api.onrender.com/"

    private val retrofit by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    private val service by lazy {
        retrofit.create(ApiService::class.java)
    }

    suspend fun uploadSnapshots(payload: List<SnapshotPayload>) =
        service.uploadSnapshots(payload)
}
