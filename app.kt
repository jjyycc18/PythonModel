'''
1. 내가 만든 메크로는 홈화면의 특정위치갑에서 클릭을 하는 기능의 메크로다. 메크로를 실행후 앱을 백그라운드로 내리고, 홈화면에서 해당위치에있는 곳에 아이콘이 클릭으로 잘 실행된다.
   그러나 백그라운드에 있는 앱에서는 실행되 메크로의 결과를 수신하지 못하고 있다, 혹시 백그라운드로 내려져서 그런가? 해결책은? 아님 다른 설정 값이 빠져서 그런가? 내가 직접 권한을 허용해야 되는 부분이 있다? (manifast permission...)
   실행되기 위해 내가 해야 되는 일을 모두 알려주고, 그게 아니라면 다시 확인 수정해라.
   
2. 현재 앱화면에서 "매크로 예약삭제" 버튼 옆에 "현재 매크로 보기" 버튼을 만들고 클릭시 예약된 매크로리스트를 표시하고, 개벌로 삭제하면 메인화면에도 해당 매크로의 "실행"버튼도 다시 활성화 하자

3. 현재 구현된 코딩을 자세한 프롬프트로 만들어줘 (다른 ai에서 코딩후 다른폴드에서 다시 만들어보고 실행해보자)
4. 노인을 위한 앱   프롬프트로 다른 폴드에 하나 만들어보자
'''

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
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
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

const val MACRO_COMPLETED_ACTION = "com.example.myapplication.MACRO_COMPLETED"

data class Macro(
    val id: Int,
    val time: String,
    val x: Int,
    val y: Int
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MacroScreen() {
    val context = LocalContext.current
    val macros = remember { mutableStateListOf<Macro>() }
    var idCounter by remember { mutableIntStateOf(0) }

    var timeInput by remember { mutableStateOf("") }
    var xInput by remember { mutableStateOf("") }
    var yInput by remember { mutableStateOf("") }

    var executionCount by remember { mutableIntStateOf(0) }
    val macroEnabledStates = remember { mutableStateMapOf<Int, Boolean>() }

    var editingMacro by remember { mutableStateOf<Macro?>(null) }

    // BroadcastReceiver to re-enable buttons and show results
    DisposableEffect(Unit) {
        val receiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context?, intent: Intent?) {
                if (intent?.action == MACRO_COMPLETED_ACTION) {
                    val id = intent.getIntExtra("id", -1)
                    val wasSuccessful = intent.getBooleanExtra("wasSuccessful", false)
                    val macro = macros.find { it.id == id }

                    if (id != -1) {
                        macroEnabledStates[id] = true
                        if (executionCount > 0) executionCount--

                        val resultMessage = if (wasSuccessful) "성공" else "실패"
                        val macroIdentifier = macro?.time ?: "ID $id"
                        Toast.makeText(context, "매크로[$macroIdentifier] 실행 $resultMessage", Toast.LENGTH_LONG).show()
                    }
                }
            }
        }
        context.registerReceiver(receiver, IntentFilter(MACRO_COMPLETED_ACTION), Context.RECEIVER_NOT_EXPORTED)
        onDispose { context.unregisterReceiver(receiver) }
    }

    // Edit Dialog
    if (editingMacro != null) {
        EditMacroDialog(
            macro = editingMacro!!,
            onDismiss = { editingMacro = null },
            onSave = { updatedMacro ->
                val index = macros.indexOfFirst { it.id == updatedMacro.id }
                if (index != -1) {
                    macros[index] = updatedMacro
                }
                editingMacro = null
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
        }) {
            Text("접근성 서비스 확인/활성화")
        }

        Spacer(modifier = Modifier.height(16.dp))

        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            OutlinedTextField(value = timeInput, onValueChange = { timeInput = it }, label = { Text("시간 (HH:mm:ss)") }, modifier = Modifier.fillMaxWidth())
            Row(Modifier.fillMaxWidth()) {
                OutlinedTextField(value = xInput, onValueChange = { xInput = it }, label = { Text("X 좌표") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number), modifier = Modifier.weight(1f))
                Spacer(modifier = Modifier.width(8.dp))
                OutlinedTextField(value = yInput, onValueChange = { yInput = it }, label = { Text("Y 좌표") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number), modifier = Modifier.weight(1f))
            }
            Spacer(modifier = Modifier.height(8.dp))
            Button(onClick = {
                val time = timeInput
                val x = xInput.toIntOrNull()
                val y = yInput.toIntOrNull()

                if (time.matches(Regex("\\d{2}:\\d{2}:\\d{2}")) && x != null && y != null) {
                    val newMacro = Macro(id = idCounter++, time = time, x = x, y = y)
                    macros.add(newMacro)
                    macroEnabledStates[newMacro.id] = true
                    timeInput = ""; xInput = ""; yInput = ""
                } else {
                    Toast.makeText(context, "입력 값을 확인해주세요. 시간 형식: HH:mm:ss", Toast.LENGTH_LONG).show()
                }
            }) { Text("매크로 추가") }
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
                            Toast.makeText(context, "최대 5개까지 실행할 수 있습니다.", Toast.LENGTH_SHORT).show()
                        }
                    },
                    onEditClick = { editingMacro = macro },
                    onDeleteClick = {
                        macros.remove(macro)
                        macroEnabledStates.remove(macro.id)
                        // Cancel the alarm if it was scheduled
                        cancelMacro(context, macro)
                    }
                )
            }
        }
    }
}

@Composable
fun MacroListItem(
    macro: Macro,
    isEnabled: Boolean,
    onExecuteClick: () -> Unit,
    onEditClick: () -> Unit,
    onDeleteClick: () -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(text = "${macro.time}, X:${macro.x}, Y:${macro.y}", modifier = Modifier.weight(1f))
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
fun EditMacroDialog(
    macro: Macro,
    onDismiss: () -> Unit,
    onSave: (Macro) -> Unit
) {
    var time by remember { mutableStateOf(macro.time) }
    var x by remember { mutableStateOf(macro.x.toString()) }
    var y by remember { mutableStateOf(macro.y.toString()) }
    val context = LocalContext.current

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("매크로 수정") },
        text = {
            Column {
                OutlinedTextField(value = time, onValueChange = { time = it }, label = { Text("시간 (HH:mm:ss)") })
                OutlinedTextField(value = x, onValueChange = { x = it }, label = { Text("X 좌표") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
                OutlinedTextField(value = y, onValueChange = { y = it }, label = { Text("Y 좌표") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    val newX = x.toIntOrNull()
                    val newY = y.toIntOrNull()
                    if (time.matches(Regex("\\d{2}:\\d{2}:\\d{2}")) && newX != null && newY != null) {
                        onSave(macro.copy(time = time, x = newX, y = newY))
                    } else {
                        Toast.makeText(context, "입력 값을 확인해주세요.", Toast.LENGTH_SHORT).show()
                    }
                }
            ) { Text("저장") }
        },
        dismissButton = { Button(onClick = onDismiss) { Text("취소") } }
    )
}

fun scheduleMacro(context: Context, macro: Macro) {
    val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
    val intent = Intent(context, MacroAlarmReceiver::class.java).apply {
        putExtra("x", macro.x)
        putExtra("y", macro.y)
        putExtra("id", macro.id)
    }
    val pendingIntent = PendingIntent.getBroadcast(context, macro.id, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
    val timeParts = macro.time.split(":").map { it.toInt() }
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
