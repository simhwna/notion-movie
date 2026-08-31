package com.notionmovie.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

// 밝은 테마 하나만. 기기 다크 모드를 보지 않는다
private val AppColors = lightColorScheme(
    primary = TextPrimary,
    onPrimary = Bg,
    secondary = TextSecondary,
    background = Bg,
    onBackground = TextPrimary,
    surface = Bg,
    onSurface = TextPrimary,
    surfaceVariant = ContainerBg,
    onSurfaceVariant = TextSecondary,
    outline = IconInactive,
    error = Danger,
    onError = Bg,
)

private val AppTypography = Typography(
    titleLarge = Title,
    titleMedium = Strong,
    bodyLarge = Body,
    bodyMedium = Body,
    bodySmall = Meta,
    labelMedium = Meta,
    labelSmall = Micro,
)

@Composable
fun NotionMovieTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = AppColors,
        typography = AppTypography,
        content = content,
    )
}
