package com.tsm.mobile.network

import com.tsm.mobile.proto.TSMServiceGrpc
import com.tsm.mobile.proto.ListSessionsRequest
import com.tsm.mobile.proto.SwitchSessionRequest
import io.grpc.ManagedChannel
import io.grpc.ManagedChannelBuilder

class NetworkManager {

    private val channel: ManagedChannel = ManagedChannelBuilder.forAddress("192.168.0.2", 50051)
        .usePlaintext()
        .build()

    private val stub: TSMServiceGrpc.TSMServiceBlockingStub = TSMServiceGrpc.newBlockingStub(channel)

    fun listSessions(userId: String) {
        val request = ListSessionsRequest.newBuilder().setUserId(userId).build()
        stub.listSessions(request)
    }

    fun switchSession(sessionId: String) {
        val request = SwitchSessionRequest.newBuilder().setSessionId(sessionId).build()
        stub.switchSession(request)
    }
}
