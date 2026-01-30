package com.example.combinedflow.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(entities = [SnapshotEntity::class], version = 1)
abstract class AppDatabase : RoomDatabase() {

    abstract fun snapshotDao(): SnapshotDao
    companion object {
        @Volatile private var INSTANCE: AppDatabase? = null

        fun getDatabase(context: Context): AppDatabase =
            INSTANCE ?: synchronized(this) {
                INSTANCE ?: Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "safety.db"
                ).build().also { INSTANCE = it }
            }
    }
}
