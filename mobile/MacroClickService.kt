package com.example.myapplication

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Intent
import android.graphics.Path
import android.os.Build
import android.view.accessibility.AccessibilityEvent
import androidx.annotation.RequiresApi

class MacroClickService : AccessibilityService() {

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onInterrupt() {}

    @RequiresApi(Build.VERSION_CODES.N)
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent != null) {
            val x = intent.getIntExtra("x", 0)
            val y = intent.getIntExtra("y", 0)
            val id = intent.getIntExtra("id", -1)
            performClick(x, y, id)
        }
        return START_STICKY
    }

    @RequiresApi(Build.VERSION_CODES.N)
    private fun performClick(x: Int, y: Int, id: Int) {
        val path = Path()
        path.moveTo(x.toFloat(), y.toFloat())
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, 100L)) // 100ms duration for click
            .build()

        dispatchGesture(gesture, object : GestureResultCallback() {
            override fun onCompleted(gestureDescription: GestureDescription?) {
                super.onCompleted(gestureDescription)
                sendCompletionBroadcast(id)
            }

            override fun onCancelled(gestureDescription: GestureDescription?) {
                super.onCancelled(gestureDescription)
                sendCompletionBroadcast(id) // Also notify on cancellation
            }
        }, null)
    }

    private fun sendCompletionBroadcast(id: Int) {
        // Create an explicit intent for the statically registered receiver
        val intent = Intent(this, MacroCompletionReceiver::class.java).apply {
            action = MACRO_COMPLETED_ACTION
            putExtra("id", id)
            // No need for wasSuccessful, as we just record the completion
        }
        sendBroadcast(intent)
    }
}
