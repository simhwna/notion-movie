package com.notionmovie.app.ui.common

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.Icon
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalHapticFeedback
import com.notionmovie.app.ui.theme.FadeMs
import com.notionmovie.app.ui.theme.ShapeEmpty
import com.notionmovie.app.ui.theme.Star
import com.notionmovie.app.ui.theme.StarIcon
import com.notionmovie.app.ui.theme.StarSmall
import com.notionmovie.app.ui.theme.TouchMin
import com.notionmovie.app.util.tick

// 탭과 좌우 드래그로 1에서 5. 값이 바뀌는 순간마다 햇핑
@Composable
fun StarRowInput(
    rating: Int,
    onRatingChange: (Int) -> Unit,
    modifier: Modifier = Modifier,
) {
    val haptic = LocalHapticFeedback.current
    val latest = rememberUpdatedState(rating)
    var width by remember { mutableIntStateOf(0) }
    Row(
        modifier = modifier
            .onSizeChanged { width = it.width }
            .pointerInput(Unit) {
                detectHorizontalDragGestures { change, _ ->
                    val total = width
                    if (total <= 0) return@detectHorizontalDragGestures
                    val ratio = change.position.x / total.toFloat()
                    val next = (ratio * 5f).toInt().coerceIn(0, 4) + 1
                    if (next != latest.value) {
                        haptic.tick()
                        onRatingChange(next)
                    }
                }
            },
        verticalAlignment = Alignment.CenterVertically,
    ) {
        for (index in 1..5) {
            val tint = animateColorAsState(
                targetValue = if (index <= rating) Star else ShapeEmpty,
                animationSpec = tween(durationMillis = FadeMs),
                label = "starTint",
            )
            Box(
                modifier = Modifier
                    .size(TouchMin)
                    .clickable {
                        if (index != rating) {
                            haptic.tick()
                            onRatingChange(index)
                        }
                    },
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    imageVector = Icons.Filled.Star,
                    contentDescription = null,
                    tint = tint.value,
                    modifier = Modifier.size(StarIcon),
                )
            }
        }
    }
}

// 기록 탭 목록의 읽기 전용 별
@Composable
fun StarRowSmall(
    rating: Int,
    modifier: Modifier = Modifier,
) {
    Row(modifier = modifier, verticalAlignment = Alignment.CenterVertically) {
        for (index in 1..5) {
            Icon(
                imageVector = Icons.Filled.Star,
                contentDescription = null,
                tint = if (index <= rating) Star else ShapeEmpty,
                modifier = Modifier.size(StarSmall),
            )
        }
    }
}
