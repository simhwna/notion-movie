package com.notionmovie.app.ui.common

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.Dp
import coil.compose.AsyncImage
import com.notionmovie.app.ui.theme.ShapeEmpty

private const val TMDB_IMAGE = "https://image.tmdb.org/t/p/w342"

// 포스터가 없으면 ShapeEmpty 도형을 그린다
@Composable
fun PosterImage(
    path: String?,
    width: Dp,
    height: Dp,
    corner: Dp,
    modifier: Modifier = Modifier,
) {
    val url = when {
        path == null || path.isBlank() -> null
        path.startsWith("http") -> path
        else -> TMDB_IMAGE + path
    }
    Box(
        modifier = modifier
            .size(width = width, height = height)
            .clip(RoundedCornerShape(corner))
            .background(ShapeEmpty)
    ) {
        if (url != null) {
            AsyncImage(
                model = url,
                contentDescription = null,
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize(),
            )
        }
    }
}
