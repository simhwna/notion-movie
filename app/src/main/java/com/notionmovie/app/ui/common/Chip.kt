package com.notionmovie.app.ui.common

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.TextStyle
import com.notionmovie.app.ui.theme.ChipMetaBg
import com.notionmovie.app.ui.theme.ChipMutedBg
import com.notionmovie.app.ui.theme.CornerChip
import com.notionmovie.app.ui.theme.Gap4
import com.notionmovie.app.ui.theme.Gap8
import com.notionmovie.app.ui.theme.Meta
import com.notionmovie.app.ui.theme.TextDisabled
import com.notionmovie.app.ui.theme.TextSheet

// 장르 칩과 IMDb 배지
@Composable
fun MetaChip(
    text: String,
    modifier: Modifier = Modifier,
    pill: Boolean = false,
) {
    Box(
        modifier = modifier
            .clip(if (pill) RoundedCornerShape(percent = 50) else RoundedCornerShape(CornerChip))
            .background(ChipMetaBg)
            .padding(horizontal = Gap8, vertical = Gap4)
    ) {
        Text(text = text, style = Meta, color = TextSheet)
    }
}

// 기록된 칩과 대기 배지
@Composable
fun MutedChip(
    text: String,
    modifier: Modifier = Modifier,
    style: TextStyle = Meta,
) {
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(CornerChip))
            .background(ChipMutedBg)
            .padding(horizontal = Gap8, vertical = Gap4)
    ) {
        Text(text = text, style = style, color = TextDisabled)
    }
}
