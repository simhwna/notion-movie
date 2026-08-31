package com.notionmovie.app.ui.common

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import com.notionmovie.app.ui.theme.CornerChip
import com.notionmovie.app.ui.theme.CornerPoster
import com.notionmovie.app.ui.theme.DotSize
import com.notionmovie.app.ui.theme.EmptyShape
import com.notionmovie.app.ui.theme.FadeMs
import com.notionmovie.app.ui.theme.Gap4
import com.notionmovie.app.ui.theme.Gap6
import com.notionmovie.app.ui.theme.Gap12
import com.notionmovie.app.ui.theme.Gap16
import com.notionmovie.app.ui.theme.ListPad
import com.notionmovie.app.ui.theme.PosterListH
import com.notionmovie.app.ui.theme.PosterListW
import com.notionmovie.app.ui.theme.ScreenPad
import com.notionmovie.app.ui.theme.ShapeEmpty
import com.notionmovie.app.ui.theme.Sub
import com.notionmovie.app.ui.theme.TextDisabled
import com.notionmovie.app.ui.theme.Track

// 중앙 안내 문구. 항상 13 회상
@Composable
fun CenterMessage(
    lines: List<String>,
    modifier: Modifier = Modifier,
    action: @Composable (() -> Unit)? = null,
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .padding(ScreenPad),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(Gap6),
        ) {
            lines.forEach { line ->
                Text(
                    text = line,
                    style = Sub,
                    color = TextDisabled,
                    textAlign = TextAlign.Center,
                )
            }
            if (action != null) {
                Spacer(modifier = Modifier.height(Gap12))
                action()
            }
        }
    }
}

// 데이터가 전혀 없을 때만 보여지는 스즜리들
@Composable
fun SkeletonRows(
    count: Int,
    modifier: Modifier = Modifier,
) {
    val pulse = remember { Animatable(0.4f) }
    LaunchedEffect(Unit) {
        while (true) {
            pulse.animateTo(1f, animationSpec = tween(durationMillis = FadeMs))
            pulse.animateTo(0.4f, animationSpec = tween(durationMillis = FadeMs))
        }
    }
    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = ListPad),
        verticalArrangement = Arrangement.spacedBy(Gap16),
    ) {
        repeat(count) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .alpha(pulse.value),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Box(
                    modifier = Modifier
                        .size(width = PosterListW, height = PosterListH)
                        .clip(RoundedCornerShape(CornerChip))
                        .background(Track)
                )
                Spacer(modifier = Modifier.width(Gap12))
                Column(verticalArrangement = Arrangement.spacedBy(Gap6)) {
                    Box(
                        modifier = Modifier
                            .width(EmptyShape * 3)
                            .height(Gap16)
                            .clip(RoundedCornerShape(CornerChip))
                            .background(Track)
                    )
                    Box(
                        modifier = Modifier
                            .width(EmptyShape * 2)
                            .height(Gap12)
                            .clip(RoundedCornerShape(CornerChip))
                            .background(Track)
                    )
                }
            }
        }
    }
}

// 기록 탭 벼 상태
@Composable
fun EmptyState(
    lines: List<String>,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .padding(ScreenPad),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(Gap6),
        ) {
            Box(
                modifier = Modifier
                    .size(EmptyShape)
                    .clip(RoundedCornerShape(percent = 50))
                    .background(ShapeEmpty)
            )
            Spacer(modifier = Modifier.height(Gap12))
            lines.forEach { line ->
                Text(
                    text = line,
                    style = Sub,
                    color = TextDisabled,
                    textAlign = TextAlign.Center,
                )
            }
        }
    }
}

// 연결 상태 점
@Composable
fun StatusDot(
    color: Color,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier
            .size(DotSize)
            .clip(RoundedCornerShape(percent = 50))
            .background(color)
    )
}

// 시트 드래그 핸들
@Composable
fun SheetHandle(modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .padding(vertical = Gap8Local)
            .size(width = com.notionmovie.app.ui.theme.HandleW, height = com.notionmovie.app.ui.theme.HandleH)
            .clip(RoundedCornerShape(percent = 50))
            .background(ShapeEmpty)
    )
}

private val Gap8Local = Gap4 * 2

// 포스터 자리 대신 쓰는 모서리 값을 한 군데에서 보기 쉬워지게 남긴다
val PosterCornerList = CornerChip
val PosterCornerSheet = CornerPoster
