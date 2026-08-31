package com.notionmovie.app.util

// 노션 내 별점은 select 문자열. 1에서 5를 다섯 자리로 만들고 읽을 때는 채운 별 갯수를 셀다
object Stars {

    fun toText(rating: Int): String {
        val filled = rating.coerceIn(0, 5)
        return "★".repeat(filled) + "☆".repeat(5 - filled)
    }

    fun fromText(text: String?): Int {
        if (text == null) return 0
        val counted = text.count { it == '★' }
        if (counted > 0) return counted.coerceAtMost(5)
        return text.trim().toIntOrNull()?.coerceIn(0, 5) ?: 0
    }
}
