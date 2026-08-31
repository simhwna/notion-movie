package com.notionmovie.app.util

import androidx.compose.ui.hapticfeedback.HapticFeedback
import androidx.compose.ui.hapticfeedback.HapticFeedbackType

// 짧은 햇핑 하나만 사용한다
fun HapticFeedback.tick() {
    performHapticFeedback(HapticFeedbackType.TextHandleMove)
}
