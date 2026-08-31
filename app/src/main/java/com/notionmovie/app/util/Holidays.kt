package com.notionmovie.app.util

import java.time.LocalDate

// 2026년 한국 고정 공휘일만 로지 테이붔로 가진다. 상달릴 공휘일과 대질공휘일은 백로그
object Holidays {

    private val fixed = setOf(
        "01-01",
        "03-01",
        "05-05",
        "06-06",
        "08-15",
        "10-03",
        "10-09",
        "12-25",
    )

    fun isHoliday(date: LocalDate): Boolean {
        val key = "%02d-%02d".format(date.monthValue, date.dayOfMonth)
        return fixed.contains(key)
    }
}
