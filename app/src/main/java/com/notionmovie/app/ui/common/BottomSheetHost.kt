package com.notionmovie.app.ui.common

import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.unit.dp
import com.notionmovie.app.ui.theme.Bg
import com.notionmovie.app.ui.theme.CornerSheet
import com.notionmovie.app.ui.theme.Dim
import com.notionmovie.app.ui.theme.FadeMs
import com.notionmovie.app.ui.theme.SheetMaxRatio
import com.notionmovie.app.ui.theme.SheetMs

// 아래에서 100ms slide, 상단 모서리만 20 라운드, 뒤 다섬
@Composable
fun BottomSheetHost(
    visible: Boolean,
    onDismiss: () -> Unit,
    content: @Composable ColumnScope.() -> Unit,
) {
    BackHandler(enabled = visible, onBack = onDismiss)
    val screenHeight = LocalConfiguration.current.screenHeightDp
    val maxHeight = (screenHeight * SheetMaxRatio).dp
    Box(modifier = Modifier.fillMaxSize()) {
        AnimatedVisibility(
            visible = visible,
            enter = fadeIn(animationSpec = tween(durationMillis = FadeMs)),
            exit = fadeOut(animationSpec = tween(durationMillis = FadeMs)),
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Dim)
                    .clickable(
                        interactionSource = remember { MutableInteractionSource() },
                        indication = null,
                    ) { onDismiss() }
            )
        }
        AnimatedVisibility(
            visible = visible,
            modifier = Modifier.align(Alignment.BottomCenter),
            enter = slideInVertically(animationSpec = tween(durationMillis = SheetMs)) { it },
            exit = slideOutVertically(animationSpec = tween(durationMillis = SheetMs)) { it },
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = maxHeight)
                    .clip(RoundedCornerShape(topStart = CornerSheet, topEnd = CornerSheet))
                    .background(Bg),
                content = content,
            )
        }
    }
}
