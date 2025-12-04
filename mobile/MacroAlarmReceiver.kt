package com.example.myapplication

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

class MacroAlarmReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        val serviceIntent = Intent(context, MacroClickService::class.java).apply {
            // Pass all extras from the original intent to the service intent
            putExtras(intent.extras ?: return)
        }
        context.startService(serviceIntent)
    }
}
