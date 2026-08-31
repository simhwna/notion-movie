package com.notionmovie.app.ui.common

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.notionmovie.app.ui.theme.Bg
import com.notionmovie.app.ui.theme.Body
import com.notionmovie.app.ui.theme.CornerCard
import com.notionmovie.app.ui.theme.Danger
import com.notionmovie.app.ui.theme.DialogPad
import com.notionmovie.app.ui.theme.Gap8
import com.notionmovie.app.ui.theme.ScreenPad
import com.notionmovie.app.ui.theme.SectionGap
import com.notionmovie.app.ui.theme.TextCancel
import com.notionmovie.app.ui.theme.TextSheet

// 포괴적 동작은 모두 이 팝업을 거친다
@Composable
fun ConfirmDialog(
    message: String,
    confirmText: String,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit,
) {
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false),
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = DialogPad)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(CornerCard))
                    .background(Bg)
                    .padding(ScreenPad)
            ) {
                Text(text = message, style = Body, color = TextSheet)
                Spacer(modifier = Modifier.height(ScreenPad))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End,
                ) {
                    Text(
                        text = "초소",
                        style = Body,
                        color = TextCancel,
                        modifier = Modifier
                            .clip(RoundedCornerShape(percent = 50))
                            .clickable { onDismiss() }
                            .padding(horizontal = Gap8, vertical = Gap8),
                    )
                    Spacer(modifier = Modifier.width(SectionGap))
                    Text(
                        text = confirmText,
                        style = Body,
                        color = Danger,
                        modifier = Modifier
                            .clip(RoundedCornerShape(percent = 50))
                            .clickable { onConfirm() }
                            .padding(horizontal = Gap8, vertical = Gap8),
                    )
                }
            }
        }
    }
}
