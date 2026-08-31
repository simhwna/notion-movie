package com.notionmovie.app.ui.common

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Movie
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.Icon
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalHapticFeedback
import com.notionmovie.app.ui.Tab
import com.notionmovie.app.ui.theme.BarGap
import com.notionmovie.app.ui.theme.BarHeight
import com.notionmovie.app.ui.theme.BarIcon
import com.notionmovie.app.ui.theme.BarTouch
import com.notionmovie.app.ui.theme.Bg
import com.notionmovie.app.ui.theme.FadeMs
import com.notionmovie.app.ui.theme.IconInactive
import com.notionmovie.app.ui.theme.TextPrimary
import com.notionmovie.app.util.tick

private fun iconOf(tab: Tab): ImageVector = when (tab) {
    Tab.RECORDS -> Icons.Outlined.Movie
    Tab.SEARCH -> Icons.Outlined.Search
    Tab.SETTINGS -> Icons.Outlined.Settings
}

private fun labelOf(tab: Tab): String = when (tab) {
    Tab.RECORDS -> "기록"
    Tab.SEARCH -> "검색"
    Tab.SETTINGS -> "설정"
}

// 아이콘 3개를 한 줄 가운데. 텍스트 라벨 없음, 선택 표시는 아이콘 색 변화만
@Composable
fun BottomBar(
    current: Tab,
    onSelect: (Tab) -> Unit,
    modifier: Modifier = Modifier,
) {
    val haptic = LocalHapticFeedback.current
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(BarHeight)
            .background(Bg),
        contentAlignment = Alignment.Center,
    ) {
        Row(
            horizontalArrangement = Arrangement.spacedBy(BarGap),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Tab.values().forEach { tab ->
                val tint = animateColorAsState(
                    targetValue = if (tab == current) TextPrimary else IconInactive,
                    animationSpec = tween(durationMillis = FadeMs),
                    label = "tabTint",
                )
                Box(
                    modifier = Modifier
                        .size(BarTouch)
                        .clip(RoundedCornerShape(percent = 50))
                        .clickable {
                            haptic.tick()
                            onSelect(tab)
                        },
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        imageVector = iconOf(tab),
                        contentDescription = labelOf(tab),
                        tint = tint.value,
                        modifier = Modifier.size(BarIcon),
                    )
                }
            }
        }
    }
}
