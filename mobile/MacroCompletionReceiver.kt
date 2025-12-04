package com.example.myapplication

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

private const val PREFS_NAME = "MacroAppPrefs"
private const val KEY_COMPLETED_MACROS = "completed_macros"

class MacroCompletionReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == MACRO_COMPLETED_ACTION) {
            val id = intent.getIntExtra("id", -1)
            if (id != -1) {
                val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                val completedIds = prefs.getStringSet(KEY_COMPLETED_MACROS, emptySet()) ?: emptySet()

                val newCompletedIds = completedIds.toMutableSet()
                newCompletedIds.add(id.toString())

                prefs.edit().putStringSet(KEY_COMPLETED_MACROS, newCompletedIds).apply()
            }
        }
    }
}
