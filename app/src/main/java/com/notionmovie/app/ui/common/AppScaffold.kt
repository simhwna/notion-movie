package com.notionmovie.app.ui.common

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.notionmovie.app.ui.Tab
import com.notionmovie.app.ui.theme.Bg

// 헤더는 맨 위, 탭 바는 맨 아래. 가운데만 내용이 들어간다
@Composable
fun AppScaffold(
    title: String,
    currentTab: Tab,
    onSelectTab: (Tab) -> Unit,
    rightActions: @Composable RowScope.() -> Unit = {},
    content: @Composable BoxScope.() -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Bg)
    ) {
        TopBar(title = title, rightActions = rightActions)
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            content = content,
        )
        BottomBar(current = currentTab, onSelect = onSelectTab)
    }
}
