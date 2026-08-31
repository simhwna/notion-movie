package com.notionmovie.app.ui.common

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalHapticFeedback
import com.notionmovie.app.ui.theme.Bg
import com.notionmovie.app.ui.theme.Body
import com.notionmovie.app.ui.theme.ChipMutedBg
import com.notionmovie.app.ui.theme.FadeMs
import com.notionmovie.app.ui.theme.PillBg
import com.notionmovie.app.ui.theme.PillHeight
import com.notionmovie.app.ui.theme.PillPad
import com.notionmovie.app.ui.theme.SaveHeight
import com.notionmovie.app.ui.theme.Strong
import com.notionmovie.app.ui.theme.TextDisabled
import com.notionmovie.app.ui.theme.TextPrimary
import com.notionmovie.app.ui.theme.TextToggleOff
import com.notionmovie.app.ui.theme.ToggleHeight
import com.notionmovie.app.util.tick

// 정렬 toggle. 선택은 검정 배경 흰 텍스트, 버전택은 PillBg
@Composable
fun TogglePill(
    text: String,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val haptic = LocalHapticFeedback.current
    val bg = animateColorAsState(
        targetValue = if (selected) TextPrimary else PillBg,
        animationSpec = tween(durationMillis = FadeMs),
        label = "toggleBg",
    )
    val fg = animateColorAsState(
        targetValue = if (selected) Bg else TextToggleOff,
        animationSpec = tween(durationMillis = FadeMs),
        label = "toggleFg",
    )
    Box(
        modifier = modifier
            .height(ToggleHeight)
            .clip(RoundedCornerShape(percent = 50))
            .background(bg.value)
            .clickable {
                haptic.tick()
                onClick()
            }
            .padding(horizontal = PillPad),
        contentAlignment = Alignment.Center,
    ) {
        Text(text = text, style = com.notionmovie.app.ui.theme.Meta, color = fg.value)
    }
}

// 관람일 값 pill
@Composable
fun ValuePill(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier
            .height(PillHeight)
            .clip(RoundedCornerShape(percent = 50))
            .background(PillBg)
            .clickable { onClick() }
            .padding(horizontal = PillPad),
        contentAlignment = Alignment.Center,
    ) {
        Text(text = text, style = Body, color = TextPrimary)
    }
}

// 재시도 등 짧은 색 pill
@Composable
fun ActionPill(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier
            .height(PillHeight)
            .clip(RoundedCornerShape(percent = 50))
            .background(TextPrimary)
            .clickable { onClick() }
            .padding(horizontal = PillPad),
        contentAlignment = Alignment.Center,
    ) {
        Text(text = text, style = Body, color = Bg)
    }
}

// 시트 저장 버튼. 별점 미선택이다면 미설정 배경
@Composable
fun SaveButton(
    text: String,
    enabled: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val haptic = LocalHapticFeedback.current
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(SaveHeight)
            .clip(RoundedCornerShape(percent = 50))
            .background(if (enabled) TextPrimary else ChipMutedBg)
            .clickable(enabled = enabled) {
                haptic.tick()
                onClick()
            },
        contentAlignment = Alignment.Center,
    ) {
        Text(
            text = text,
            style = Strong,
            color = if (enabled) Bg else TextDisabled,
        )
    }
}
