package com.tsm.mobile.util

import org.json.JSONObject

data class QRCodeData(
    val sessionId: String,
    val sessionKey: String
)

class QRCodeParser {

    fun parse(jsonString: String): QRCodeData? {
        return try {
            val jsonObject = JSONObject(jsonString)
            val sessionId = jsonObject.getString("session_id")
            val sessionKey = jsonObject.getString("session_key")
            QRCodeData(sessionId, sessionKey)
        } catch (e: Exception) {
            null
        }
    }
}
