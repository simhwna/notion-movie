package com.notionmovie.app.util

import java.time.LocalDate
import java.time.format.DateTimeFormatter

// 저장은 ISO yyyy-MM-dd, 화면 표기는 2026.08.30
object Dates {

    private val ISO: DateTimeFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd")
    private val DOT: DateTimeFormatter = DateTimeFormatter.ofPattern("yyyy.MM.dd")
    private val MONTH: DateTimeFormatter = DateTimeFormatter.ofPattern("yyyy.MM")

    fun today(): LocalDate = LocalDate.now()

    fun toIso(date: LocalDate): String = date.format(ISO)

    fun parse(text: String?): LocalDate? {
        if (text == null || text.isBlank()) return null
        val parts = text.trim()
            .replace('.', '-')
            .replace('/', '-')
            .split('-')
            .filter { it.isNotBlank() }
        if (parts.size < 3) return null
        val year = parts[0].toIntOrNull() ?: return null
        val month = parts[1].toIntOrNull() ?: return null
        val day = parts[2].toIntOrNull() ?: return null
        return runCatching { LocalDate.of(year, month, day) }.getOrNull()
    }

    fun display(iso: String?): String {
        val date = parse(iso) ?: return ""
        return date.format(DOT)
    }

    fun display(date: LocalDate): String = date.format(DOT)

    fun displayMonth(date: LocalDate): String = date.format(MONTH)

    fun normalizeToIso(text: String?): String? {
        val date = parse(text) ?: return null
        return toIso(date)
    }
}
