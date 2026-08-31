package com.notionmovie.app.ui.common

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import com.notionmovie.app.ui.theme.BarEdge
import com.notionmovie.app.ui.theme.BarGap
import com.notionmovie.app.ui.theme.BarHeight
import com.notionmovie.app.ui.theme.BarIcon
import com.notionmovie.app.ui.theme.BarTouch
import com.notionmovie.app.ui.theme.Bg
import com.notionmovie.app.ui.theme.IconInactive
import com.notionmovie.app.ui.theme.TextPrimary
import com.notionmovie.app.ui.theme.Title
import com.notionmovie.app.ui.theme.TitleGuard
import com.notionmovie.app.util.tick

// 상단 헤더. 섹션 5 바 관과 서로 같은 수치를 본다
@Composable
fun TopBar(
    title: String,
    modifier: Modifier = Modifier,
    leftActions: @Composable RowScope.() -> Unit = {},
    rightActions: @Composable RowScope.() -> Unit = {},
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(BarHeight)
            .background(Bg)
    ) {
        Text(
            text = title,
            style = Title,
            color = TextPrimary,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            textAlign = TextAlign.Center,
            modifier = Modifier
                .align(Alignment.Center)
                .fillMaxWidth()
                .padding(horizontal = TitleGuard),
        )
        Row(
            modifier = Modifier
                .align(Alignment.CenterStart)
                .padding(start = BarEdge),
            horizontalArrangement = Arrangement.spacedBy(BarGap),
            verticalAlignment = Alignment.CenterVertically,
            content = leftActions,
        )
        Row(
            modifier = Modifier
                .align(Alignment.CenterEnd)
                .padding(end = BarEdge),
            horizontalArrangement = Arrangement.spacedBy(BarGap),
            verticalAlignment = Alignment.CenterVertically,
            content = rightActions,
        )
    }
}

// 동작하지 않는 버튼은 지우지 않고 회상으로 남긴다
@Composable
fun BarIconButton(
    icon: ImageVector,
    label: String,
    enabled: Boolean = true,
    spinning: Boolean = false,
    onClick: () -> Unit,
) {
    val haptic = LocalHapticFeedback.current
    val angle = remember { Animatable(0f) }
    LaunchedEffect(spinning) {
        if (!spinning) {
            angle.snapTo(0f)
            return@LaunchedEffect
        }
        while (true) {
            angle.snapTo(0f)
            angle.animateTo(360f, animationSpec = tween(durationMillis = 800, easing = LinearEasing))
        }
    }
    Box(
        modifier = Modifier
            .size(BarTouch)
            .clip(RoundedCornerShape(percent = 50))
            .clickable(enabled = enabled) {
                haptic.tick()
                onClick()
            },
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            imageVector = icon,
            contentDescription = label,
            tint = if (enabled) TextPrimary else IconInactive,
            modifier = Modifier
                .size(BarIcon)
                .rotate(angle.value),
        )
    }
}
