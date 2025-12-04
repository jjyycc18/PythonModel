package com.example.myapplication

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Bundle
import android.provider.Settings
import android.text.TextUtils
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.DefaultLifecycleObserver
import androidx.lifecycle.LifecycleOwner
import com.example.myapplication.ui.theme.MyApplicationTheme
import java.util.*

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MyApplicationTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    MacroScreen()
                }
            }
        }
    }
}

// --- Constants and Data Class ---
const val MACRO_COMPLETED_ACTION = "com.example.myapplication.MACRO_COMPLETED"
private const val PREFS_NAME = "MacroAppPrefs"
private const val KEY_MACROS = "macros"
private const val KEY_ID_COUNTER = "id_counter"
private const val KEY_COMPLETED_MACROS = "completed_macros"

data class Macro(
    val id: Int,
    val time: String,
    val x: Int,
    val y: Int
)

// --- Main Composable ---
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MacroScreen() {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    val (initialMacros, initialIdCounter) = remember { loadMacros(context) }
    val macros = remember { mutableStateListOf(*initialMacros.toTypedArray()) }
    var idCounter by remember { mutableIntStateOf(initialIdCounter) }

    var timeInput by remember { mutableStateOf("") }
    var xInput by remember { mutableStateOf("") }
    var yInput by remember { mutableStateOf("") }

    var executionCount by remember { mutableIntStateOf(0) }
    val macroEnabledStates = remember { mutableStateMapOf<Int, Boolean>() }

    var editingMacro by remember { mutableStateOf<Macro?>(null) }
    var showScheduledMacrosDialog by remember { mutableStateOf(false) }

    fun saveData() = saveMacros(context, macros.toList(), idCounter)

    // Lifecycle observer to sync state on resume from background
    DisposableEffect(lifecycleOwner, macros.size) {
        val observer = object : DefaultLifecycleObserver {
            override fun onResume(owner: LifecycleOwner) {
                // 1. Check for macros completed in the background and update UI
                val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                val completedIds = prefs.getStringSet(KEY_COMPLETED_MACROS, null)?.mapNotNull { it.toIntOrNull() }?.toSet() ?: emptySet()

                if (completedIds.isNotEmpty()) {
                    completedIds.forEach { id ->
                        if (macroEnabledStates[id] == false) { // Update only if it was running
                            macroEnabledStates[id] = true
                            Toast.makeText(context, "백그라운드 매크로(ID:$id) 완료 처리", Toast.LENGTH_SHORT).show()
                        }
                    }
                    // Clear the completed list after processing
                    prefs.edit().remove(KEY_COMPLETED_MACROS).apply()
                }

                // 2. Sync currently scheduled (running) macros states
                var runningCount = 0
                macros.forEach { macro ->
                    if (isMacroScheduled(context, macro)) {
                        if (macroEnabledStates.getOrPut(macro.id) { true }) {
                             macroEnabledStates[macro.id] = false // Sync to running state
                        }
                        runningCount++
                    } else {
                         if (!macroEnabledStates.getOrPut(macro.id) { true }) {
                            macroEnabledStates[macro.id] = true // Sync to available state
                        }
                    }
                }
                executionCount = runningCount
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }


    if (editingMacro != null) {
        EditMacroDialog(
            macro = editingMacro!!,
            onDismiss = { editingMacro = null },
            onSave = { updatedMacro ->
                val index = macros.indexOfFirst { it.id == updatedMacro.id }
                if (index != -1) {
                    cancelMacro(context, macros[index])
                    macros[index] = updatedMacro
                    macroEnabledStates[updatedMacro.id] = true
                    saveData()
                }
                editingMacro = null
            }
        )
    }

    if (showScheduledMacrosDialog) {
        ScheduledMacrosDialog(
            macros = macros,
            macroEnabledStates = macroEnabledStates,
            onDismiss = { showScheduledMacrosDialog = false },
            onCancelMacro = {
                cancelMacro(context, it)
                macroEnabledStates[it.id] = true
                if (executionCount > 0) executionCount--
                Toast.makeText(context, "${it.time} 예약을 취소했습니다.", Toast.LENGTH_SHORT).show()
            }
        )
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Button(onClick = {
            if (!isAccessibilityServiceEnabled(context, MacroClickService::class.java)) {
                Toast.makeText(context, "접근성 서비스 메뉴로 이동합니다.", Toast.LENGTH_LONG).show()
                context.startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            }
        }) { Text("접근성 서비스 확인/활성화") }

        Spacer(modifier = Modifier.height(16.dp))

        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            OutlinedTextField(value = timeInput, onValueChange = { timeInput = it }, label = { Text("시간 (HH.mm.ss)") }, modifier = Modifier.fillMaxWidth())
            Row(Modifier.fillMaxWidth()) {
                OutlinedTextField(value = xInput, onValueChange = { xInput = it }, label = { Text("X 좌표") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number), modifier = Modifier.weight(1f))
                Spacer(modifier = Modifier.width(8.dp))
                OutlinedTextField(value = yInput, onValueChange = { yInput = it }, label = { Text("Y 좌표") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number), modifier = Modifier.weight(1f))
            }
            Spacer(modifier = Modifier.height(8.dp))
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(modifier = Modifier.weight(1f), onClick = {
                    if (timeInput.matches(Regex("\\d{2}\\.\\d{2}\\.\\d{2}")) && xInput.toIntOrNull() != null && yInput.toIntOrNull() != null) {
                        val newMacro = Macro(id = idCounter++, time = timeInput, x = xInput.toInt(), y = yInput.toInt())
                        macros.add(newMacro)
                        macroEnabledStates[newMacro.id] = true
                        timeInput = ""; xInput = ""; yInput = ""
                        saveData()
                    } else {
                        Toast.makeText(context, "입력 값을 확인해주세요. 시간 형식: HH.mm.ss", Toast.LENGTH_LONG).show()
                    }
                }) { Text("추가", fontSize = 12.sp) }

                Button(modifier = Modifier.weight(1f), onClick = { showScheduledMacrosDialog = true }) { Text("예약 보기", fontSize = 12.sp) }

                Button(modifier = Modifier.weight(1f), onClick = {
                    var cancelledCount = 0
                    macros.forEach { macro ->
                        if (macroEnabledStates[macro.id] == false) {
                            cancelMacro(context, macro)
                            macroEnabledStates[macro.id] = true
                            cancelledCount++
                        }
                    }
                    if (cancelledCount > 0) {
                        executionCount = 0
                        Toast.makeText(context, "$cancelledCount 개의 예약을 모두 취소했습니다.", Toast.LENGTH_SHORT).show()
                    } else {
                        Toast.makeText(context, "취소할 예약된 매크로가 없습니다.", Toast.LENGTH_SHORT).show()
                    }
                }) { Text("전체 삭제", fontSize = 12.sp) }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))
        Divider()

        LazyColumn(modifier = Modifier.fillMaxSize()) {
            items(macros, key = { it.id }) { macro ->
                MacroListItem(
                    macro = macro,
                    isEnabled = macroEnabledStates.getOrPut(macro.id) { true },
                    onExecuteClick = {
                        if (executionCount < 5) {
                            executionCount++
                            macroEnabledStates[macro.id] = false
                            scheduleMacro(context, macro)
                        } else {
                            Toast.makeText(context, "최대 5개까지 동시 실행할 수 있습니다.", Toast.LENGTH_SHORT).show()
                        }
                    },
                    onEditClick = { editingMacro = macro },
                    onDeleteClick = {
                        if (macroEnabledStates[macro.id] == false) {
                            if (executionCount > 0) executionCount--
                        }
                        macros.remove(macro)
                        macroEnabledStates.remove(macro.id)
                        cancelMacro(context, macro)
                        saveData()
                    }
                )
            }
        }
    }
}

@Composable
fun MacroListItem(
    macro: Macro, isEnabled: Boolean, onExecuteClick: () -> Unit,
    onEditClick: () -> Unit, onDeleteClick: () -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(text = "${macro.time}, X:${macro.x}, Y:${macro.y}", modifier = Modifier.weight(1f), maxLines = 1)
        Row {
            Button(onClick = onExecuteClick, enabled = isEnabled) { Text("실행") }
            Spacer(modifier = Modifier.width(4.dp))
            Button(onClick = onEditClick) { Text("수정") }
            Spacer(modifier = Modifier.width(4.dp))
            Button(onClick = onDeleteClick, colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)) { Text("삭제") }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EditMacroDialog(macro: Macro, onDismiss: () -> Unit, onSave: (Macro) -> Unit) {
    var time by remember { mutableStateOf(macro.time) }
    var x by remember { mutableStateOf(macro.x.toString()) }
    var y by remember { mutableStateOf(macro.y.toString()) }
    val context = LocalContext.current

    AlertDialog(
        onDismissRequest = onDismiss, title = { Text("매크로 수정") },
        text = {
            Column {
                OutlinedTextField(value = time, onValueChange = { time = it }, label = { Text("시간 (HH.mm.ss)") })
                OutlinedTextField(value = x, onValueChange = { x = it }, label = { Text("X 좌표") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
                OutlinedTextField(value = y, onValueChange = { y = it }, label = { Text("Y 좌표") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
            }
        },
        confirmButton = {
            Button(onClick = {
                if (time.matches(Regex("\\d{2}\\.\\d{2}\\.\\d{2}")) && x.toIntOrNull() != null && y.toIntOrNull() != null) {
                    onSave(macro.copy(time = time, x = x.toInt(), y = y.toInt()))
                } else {
                    Toast.makeText(context, "입력 값을 확인해주세요. 시간 형식: HH.mm.ss", Toast.LENGTH_SHORT).show()
                }
            }) { Text("저장") }
        },
        dismissButton = { Button(onClick = onDismiss) { Text("취소") } }
    )
}

@Composable
fun ScheduledMacrosDialog(
    macros: List<Macro>,
    macroEnabledStates: Map<Int, Boolean>,
    onDismiss: () -> Unit,
    onCancelMacro: (Macro) -> Unit
) {
    val scheduledMacros = macros.filter { macroEnabledStates[it.id] == false }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("예약된 매크로 목록") },
        text = {
            if (scheduledMacros.isEmpty()) {
                Text("현재 예약된 매크로가 없습니다.")
            } else {
                LazyColumn {
                    items(scheduledMacros, key = { it.id }) { macro ->
                        Row(
                            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("${macro.time}, X:${macro.x}, Y:${macro.y}", modifier = Modifier.weight(1f), maxLines = 1)
                            Button(
                                onClick = { onCancelMacro(macro) },
                                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
                            ) {
                                Text("삭제")
                            }
                        }
                    }
                }
            }
        },
        confirmButton = {
            Button(onClick = onDismiss) {
                Text("닫기")
            }
        }
    )
}


fun saveMacros(context: Context, macros: List<Macro>, idCounter: Int) {
    val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE).edit()
    val macroSet = macros.map { "${it.id}|${it.time}|${it.x}|${it.y}" }.toSet()
    prefs.putStringSet(KEY_MACROS, macroSet)
    prefs.putInt(KEY_ID_COUNTER, idCounter)
    prefs.apply()
}

fun loadMacros(context: Context): Pair<List<Macro>, Int> {
    val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    val macroSet = prefs.getStringSet(KEY_MACROS, emptySet()) ?: emptySet()
    val idCounter = prefs.getInt(KEY_ID_COUNTER, 0)
    val macros = macroSet.mapNotNull {
        try {
            val parts = it.split('|')
            if (parts.size == 4) Macro(parts[0].toInt(), parts[1], parts[2].toInt(), parts[3].toInt()) else null
        } catch (e: Exception) { null }
    }.sortedBy { it.id }
    return Pair(macros, idCounter)
}

fun scheduleMacro(context: Context, macro: Macro) {
    val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
    val intent = Intent(context, MacroAlarmReceiver::class.java).apply {
        putExtra("x", macro.x)
        putExtra("y", macro.y)
        putExtra("id", macro.id)
    }
    val pendingIntent = PendingIntent.getBroadcast(context, macro.id, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
    val timeParts = macro.time.split(".").map { it.toInt() } // Changed to split by dot
    val calendar = Calendar.getInstance().apply {
        set(Calendar.HOUR_OF_DAY, timeParts[0])
        set(Calendar.MINUTE, timeParts[1])
        set(Calendar.SECOND, timeParts[2])
        if (before(Calendar.getInstance())) { add(Calendar.DATE, 1) }
    }
    try {
        if (alarmManager.canScheduleExactAlarms()) {
            alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, calendar.timeInMillis, pendingIntent)
            Toast.makeText(context, "${macro.time}에 매크로가 예약되었습니다.", Toast.LENGTH_SHORT).show()
        } else {
            Toast.makeText(context, "정확한 알람 예약 권한이 필요합니다.", Toast.LENGTH_LONG).show()
            context.startActivity(Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM))
        }
    } catch (e: SecurityException) {
        Toast.makeText(context, "정확한 알람 예약 권한이 필요합니다.", Toast.LENGTH_LONG).show()
    }
}

fun cancelMacro(context: Context, macro: Macro) {
    val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
    val intent = Intent(context, MacroAlarmReceiver::class.java)
    val pendingIntent = PendingIntent.getBroadcast(context, macro.id, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
    alarmManager.cancel(pendingIntent)
}

fun isMacroScheduled(context: Context, macro: Macro): Boolean {
    val intent = Intent(context, MacroAlarmReceiver::class.java)
    val pendingIntent = PendingIntent.getBroadcast(context, macro.id, intent, PendingIntent.FLAG_NO_CREATE or PendingIntent.FLAG_IMMUTABLE)
    return pendingIntent != null
}

fun isAccessibilityServiceEnabled(context: Context, service: Class<*>): Boolean {
    val am = context.getSystemService(Context.ACCESSIBILITY_SERVICE) as android.view.accessibility.AccessibilityManager
    val enabledServices = Settings.Secure.getString(context.contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES)
    if (enabledServices == null) return false
    val colonSplitter = TextUtils.SimpleStringSplitter(':')
    colonSplitter.setString(enabledServices)
    while (colonSplitter.hasNext()) {
        val componentName = colonSplitter.next()
        val enabledService = ComponentName.unflattenFromString(componentName)
        if (enabledService?.packageName == context.packageName && enabledService.className == service.name) {
            return true
        }
    }
    return false
}
