// TSM Android Implementation
// Complete Android app architecture for Telegram Session Manager

// ============================================================================
// 1. APP STRUCTURE & DEPENDENCIES
// ============================================================================

// build.gradle.kts (Module: app)
"""
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("kotlin-kapt")
    id("dagger.hilt.android.plugin")
    id("kotlinx-serialization")
}

android {
    namespace = "com.tsm.mobile"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.tsm.mobile"
        minSdk = 26  // Android 8.0+ for security features
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.8"
    }

    signingConfigs {
        create("release") {
            // Use environment variables for CI/CD
            storeFile = file(System.getenv("KEYSTORE_FILE") ?: "release.keystore")
            storePassword = System.getenv("KEYSTORE_PASSWORD")
            keyAlias = System.getenv("KEY_ALIAS")
            keyPassword = System.getenv("KEY_PASSWORD")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            signingConfig = signingConfigs.getByName("release")
        }
    }
}

@Composable
fun SearchResultsScreen(results: List<String>) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Text("Search Results", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(16.dp))
        if (results.isEmpty()) {
            Text("No results found.")
        } else {
            LazyColumn {
                items(results) { result ->
                    Text(result)
                }
            }
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.activity:activity-compose:1.8.2")
    
    // Jetpack Compose
    implementation(platform("androidx.compose:compose-bom:2024.02.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    
    // Security & Crypto
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
    implementation("androidx.biometric:biometric:1.2.0-alpha05")
    implementation("com.google.crypto.tink:tink-android:1.9.0")
    
    // Networking
    implementation("io.grpc:grpc-android:1.59.0")
    implementation("io.grpc:grpc-kotlin-stub:1.4.0")
    implementation("io.grpc:grpc-protobuf:1.59.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    
    // Dependency Injection
    implementation("com.google.dagger:hilt-android:2.48")
    kapt("com.google.dagger:hilt-compiler:2.48")
    implementation("androidx.hilt:hilt-navigation-compose:1.1.0")
    
    // Data & Serialization
    implementation("androidx.datastore:datastore-preferences:1.0.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.2")
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    kapt("androidx.room:room-compiler:2.6.1")
    
    // Background Work
    implementation("androidx.work:work-runtime-ktx:2.9.0")
    
    // QR Code
    implementation("com.google.mlkit:barcode-scanning:17.2.0")
    implementation("com.journeyapps:zxing-android-embedded:4.3.0")
}
"""

// ============================================================================
// 2. MAIN APPLICATION CLASS
// ============================================================================

package com.tsm.mobile

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import androidx.hilt.work.HiltWorkerFactory
import androidx.work.Configuration
import com.google.crypto.tink.Aead
import com.google.crypto.tink.Config
import com.google.crypto.tink.KeysetHandle
import com.google.crypto.tink.aead.AeadConfig
import com.google.crypto.tink.integration.android.AndroidKeysetManager
import dagger.hilt.android.HiltAndroidApp
import javax.inject.Inject

@HiltAndroidApp
class TSMApplication : Application(), Configuration.Provider {
    
    @Inject lateinit var workerFactory: HiltWorkerFactory
    
    override fun onCreate() {
        super.onCreate()
        
        // Initialize security
        initializeSecurity()
        
        // Create notification channels
        createNotificationChannels()
        
        // Setup crash reporting (in production)
        setupCrashReporting()
    }
    
    private fun initializeSecurity() {
        // Initialize Tink for cryptography
        try {
            AeadConfig.register()
            Config.register(AeadConfig.LATEST)
        } catch (e: Exception) {
            // Handle initialization failure
        }
        
        // Verify app signature (anti-tampering)
        if (!SecurityUtils.verifyAppSignature(this)) {
            // App has been tampered with
            throw SecurityException("App integrity check failed")
        }
    }
    
    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val notificationManager = getSystemService(NotificationManager::class.java)
            
            // Security alerts channel
            val securityChannel = NotificationChannel(
                CHANNEL_SECURITY,
                "Security Alerts",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Critical security notifications"
                enableVibration(true)
                setShowBadge(true)
            }
            
            // Session updates channel
            val sessionChannel = NotificationChannel(
                CHANNEL_SESSION,
                "Session Updates",
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply {
                description = "Session switch notifications"
            }
            
            notificationManager.createNotificationChannels(
                listOf(securityChannel, sessionChannel)
            )
        }
    }
    
    private fun setupCrashReporting() {
        // In production, use Firebase Crashlytics or similar
        Thread.setDefaultUncaughtExceptionHandler { _, e ->
            // Log crash securely without leaking sensitive data
            SecurityLogger.logCrash(e)
        }
    }
    
    override fun getWorkManagerConfiguration(): Configuration {
        return Configuration.Builder()
            .setWorkerFactory(workerFactory)
            .build()
    }
    
    companion object {
        const val CHANNEL_SECURITY = "tsm_security"
        const val CHANNEL_SESSION = "tsm_session"
    }
}

// ============================================================================
// 3. SECURITY MANAGER
// ============================================================================

package com.tsm.mobile.security

import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity
import com.google.crypto.tink.Aead
import com.google.crypto.tink.integration.android.AndroidKeysetManager
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.suspendCancellableCoroutine
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

@Singleton
class SecurityManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val keyAlias = "TSM_MASTER_KEY"
    private val androidKeyStore = "AndroidKeyStore"
    
    // Tink AEAD for data encryption
    private val aead: Aead by lazy {
        AndroidKeysetManager.Builder()
            .withSharedPref(context, "tsm_keyset", "tsm_keyset_prefs")
            .withKeyTemplate(com.google.crypto.tink.aead.AesGcmKeyManager.aes256GcmTemplate())
            .withMasterKeyUri("android-keystore://$keyAlias")
            .build()
            .keysetHandle
            .getPrimitive(Aead::class.java)
    }
    
    /**
     * Initialize biometric authentication
     */
    suspend fun authenticateBiometric(activity: FragmentActivity): BiometricResult {
        return suspendCancellableCoroutine { continuation ->
            val executor = ContextCompat.getMainExecutor(activity)
            val biometricPrompt = BiometricPrompt(
                activity,
                executor,
                object : BiometricPrompt.AuthenticationCallback() {
                    override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                        super.onAuthenticationSucceeded(result)
                        continuation.resume(BiometricResult.Success)
                    }
                    
                    override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                        super.onAuthenticationError(errorCode, errString)
                        continuation.resume(
                            BiometricResult.Error(errorCode, errString.toString())
                        )
                    }
                    
                    override fun onAuthenticationFailed() {
                        super.onAuthenticationFailed()
                        // Don't cancel here, let user retry
                    }
                }
            )
            
            val promptInfo = BiometricPrompt.PromptInfo.Builder()
                .setTitle("TSM Authentication")
                .setSubtitle("Verify your identity to access sessions")
                .setAllowedAuthenticators(
                    BiometricManager.Authenticators.BIOMETRIC_STRONG or
                    BiometricManager.Authenticators.DEVICE_CREDENTIAL
                )
                .build()
            
            biometricPrompt.authenticate(promptInfo)
            
            continuation.invokeOnCancellation {
                biometricPrompt.cancelAuthentication()
            }
        }
    }
    
    /**
     * Encrypt sensitive data using Tink
     */
    fun encrypt(plaintext: ByteArray): ByteArray {
        return aead.encrypt(plaintext, null)
    }
    
    /**
     * Decrypt data using Tink
     */
    fun decrypt(ciphertext: ByteArray): ByteArray {
        return aead.decrypt(ciphertext, null)
    }
    
    /**
     * Generate or retrieve hardware-backed key
     */
    private fun getOrCreateSecretKey(): SecretKey {
        val keyStore = KeyStore.getInstance(androidKeyStore).apply { load(null) }
        
        return if (keyStore.containsAlias(keyAlias)) {
            (keyStore.getEntry(keyAlias, null) as KeyStore.SecretKeyEntry).secretKey
        } else {
            val keyGenerator = KeyGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_AES,
                androidKeyStore
            )
            
            val keyGenParameterSpec = KeyGenParameterSpec.Builder(
                keyAlias,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
            ).apply {
                setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                setKeySize(256)
                setUserAuthenticationRequired(true)
                
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                    setInvalidatedByBiometricEnrollment(true)
                }
                
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                    setUnlockedDeviceRequired(true)
                    setIsStrongBoxBacked(true) // Use StrongBox if available
                }
            }.build()
            
            keyGenerator.init(keyGenParameterSpec)
            keyGenerator.generateKey()
        }
    }
    
    /**
     * Verify app hasn't been tampered with
     */
    fun verifyIntegrity(): Boolean {
        return try {
            val packageInfo = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                context.packageManager.getPackageInfo(
                    context.packageName,
                    PackageManager.GET_SIGNING_CERTIFICATES
                )
            } else {
                @Suppress("DEPRECATION")
                context.packageManager.getPackageInfo(
                    context.packageName,
                    PackageManager.GET_SIGNATURES
                )
            }
            
            val signatures = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                packageInfo.signingInfo.apkContentsSigners
            } else {
                @Suppress("DEPRECATION")
                packageInfo.signatures
            }
            
            // Verify against known signature hash
            val currentHash = signatures.map { 
                it.toByteArray().toSHA256() 
            }.firstOrNull()
            
            currentHash == BuildConfig.EXPECTED_SIGNATURE_HASH
        } catch (e: Exception) {
            false
        }
    }
    
    sealed class BiometricResult {
        object Success : BiometricResult()
        data class Error(val code: Int, val message: String) : BiometricResult()
    }
}

// ============================================================================
// 4. NETWORK LAYER - GRPC CLIENT
// ============================================================================

package com.tsm.mobile.network

import android.content.Context
import com.tsm.mobile.proto.*
import dagger.hilt.android.qualifiers.ApplicationContext
import io.grpc.ManagedChannel
import io.grpc.android.AndroidChannelBuilder
import io.grpc.okhttp.OkHttpChannelBuilder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.withContext
import java.security.cert.CertificateFactory
import java.security.cert.X509Certificate
import javax.inject.Inject
import javax.inject.Singleton
import javax.net.ssl.*

@Singleton
class TSMNetworkClient @Inject constructor(
    @ApplicationContext private val context: Context,
    private val securityManager: SecurityManager,
    private val sessionManager: SessionManager
) {
    private var channel: ManagedChannel? = null
    private var stub: TSMobileGrpcKt.TSMobileCoroutineStub? = null
    
    /**
     * Connect to TSM desktop server
     */
    suspend fun connect(host: String, port: Int) = withContext(Dispatchers.IO) {
        // Load pinned certificate
        val pinnedCert = loadPinnedCertificate()
        
        // Create custom SSL context with certificate pinning
        val sslContext = createPinnedSSLContext(pinnedCert)
        
        // Build channel with custom SSL
        channel = OkHttpChannelBuilder
            .forAddress(host, port)
            .sslSocketFactory(sslContext.socketFactory)
            .hostnameVerifier { hostname, _ ->
                // Verify hostname matches expected pattern
                hostname == "tsm.local" || hostname.endsWith(".tsm.local")
            }
            .build()
        
        stub = TSMobileGrpcKt.TSMobileCoroutineStub(channel!!)
    }
    
    /**
     * Authenticate with OPAQUE protocol
     */
    suspend fun authenticate(deviceName: String): AuthResult = withContext(Dispatchers.IO) {
        try {
            // Phase 1: Initialize
            val initRequest = authRequest {
                step = "init"
                clientId = sessionManager.getDeviceId()
                platform = "android"
                version = BuildConfig.VERSION_NAME
                this.deviceName = deviceName
            }
            
            val initResponse = stub!!.authenticate(initRequest)
            
            // Phase 2: OPAQUE verification
            val proof = generateOPAQUEProof(initResponse.serverData)
            
            val verifyRequest = authRequest {
                step = "verify"
                clientId = sessionManager.getDeviceId()
                clientProof = Base64.encodeToString(proof, Base64.NO_WRAP)
            }
            
            val finalResponse = stub!!.authenticate(verifyRequest)
            
            // Store session
            sessionManager.saveSession(
                sessionId = finalResponse.sessionId,
                encryptionKey = Base64.decode(finalResponse.encryptionKey, Base64.NO_WRAP)
            )
            
            AuthResult.Success(finalResponse.sessionId)
        } catch (e: Exception) {
            AuthResult.Error(e.message ?: "Authentication failed")
        }
    }
    
    /**
     * List available Telegram sessions
     */
    fun listSessions(): Flow<List<RemoteSession>> = flow {
        val session = sessionManager.getActiveSession()
            ?: throw IllegalStateException("Not authenticated")
        
        val request = listRequest {
            sessionId = session.sessionId
            signature = generateRequestSignature()
        }
        
        val response = stub!!.listSessions(request)
        
        // Decrypt response
        val decrypted = securityManager.decrypt(
            Base64.decode(response.encryptedData, Base64.NO_WRAP)
        )
        
        val sessionList = Json.decodeFromString<SessionListResponse>(
            decrypted.decodeToString()
        )
        
        emit(sessionList.sessions.map { it.toRemoteSession() })
    }
    
    /**
     * Switch active Telegram session
     */
    suspend fun switchSession(targetSessionId: String): SwitchResult = 
        withContext(Dispatchers.IO) {
            try {
                val session = sessionManager.getActiveSession()
                    ?: throw IllegalStateException("Not authenticated")
                
                // Encrypt request
                val requestData = Json.encodeToString(
                    SwitchSessionRequest(targetSessionId)
                )
                val encrypted = securityManager.encrypt(requestData.toByteArray())
                
                val request = switchRequest {
                    sessionId = session.sessionId
                    signature = generateRequestSignature()
                    encryptedData = Base64.encodeToString(encrypted, Base64.NO_WRAP)
                    nonce = Base64.encodeToString(generateNonce(), Base64.NO_WRAP)
                }
                
                val response = stub!!.switchSession(request)
                
                // Decrypt response
                val decrypted = securityManager.decrypt(
                    Base64.decode(response.encryptedData, Base64.NO_WRAP)
                )
                
                val result = Json.decodeFromString<SwitchResponse>(
                    decrypted.decodeToString()
                )
                
                if (result.success) {
                    SwitchResult.Success(result.message)
                } else {
                    SwitchResult.Error(result.message)
                }
            } catch (e: Exception) {
                SwitchResult.Error(e.message ?: "Switch failed")
            }
        }
    
    /**
     * Emergency wipe all sessions
     */
    suspend fun emergencyWipe(panicCode: String): Boolean = withContext(Dispatchers.IO) {
        try {
            val session = sessionManager.getActiveSession()
                ?: throw IllegalStateException("Not authenticated")
            
            val request = wipeRequest {
                sessionId = session.sessionId
                signature = generateRequestSignature()
                this.panicCode = panicCode
            }
            
            val response = stub!!.emergencyWipe(request)
            response.success
        } catch (e: Exception) {
            false
        }
    }
    
    private fun loadPinnedCertificate(): X509Certificate {
        // Load certificate from assets
        context.assets.open("tsm_server.crt").use { certStream ->
            val cf = CertificateFactory.getInstance("X.509")
            return cf.generateCertificate(certStream) as X509Certificate
        }
    }
    
    private fun createPinnedSSLContext(pinnedCert: X509Certificate): SSLContext {
        // Create trust manager that only trusts our certificate
        val trustManager = object : X509TrustManager {
            override fun checkClientTrusted(chain: Array<out X509Certificate>?, authType: String?) {
                // Not used for client
            }
            
            override fun checkServerTrusted(chain: Array<out X509Certificate>?, authType: String?) {
                if (chain.isNullOrEmpty()) {
                    throw SSLException("Server certificate chain is empty")
                }
                
                // Verify server cert matches pinned cert
                if (!chain[0].equals(pinnedCert)) {
                    throw SSLException("Server certificate does not match pinned certificate")
                }
            }
            
            override fun getAcceptedIssuers(): Array<X509Certificate> = arrayOf(pinnedCert)
        }
        
        return SSLContext.getInstance("TLS").apply {
            init(null, arrayOf(trustManager), null)
        }
    }
    
    private fun generateOPAQUEProof(serverData: String): ByteArray {
        // Simplified - in production use proper OPAQUE library
        return securityManager.encrypt("opaque_proof".toByteArray())
    }
    
    private fun generateRequestSignature(): String {
        // Generate HMAC signature for request
        return "signature_placeholder"
    }
    
    private fun generateNonce(): ByteArray {
        return ByteArray(12).apply {
            java.security.SecureRandom().nextBytes(this)
        }
    }
    
    fun disconnect() {
        channel?.shutdown()
        channel = null
        stub = null
    }
    
    sealed class AuthResult {
        data class Success(val sessionId: String) : AuthResult()
        data class Error(val message: String) : AuthResult()
    }
    
    sealed class SwitchResult {
        data class Success(val message: String) : SwitchResult()
        data class Error(val message: String) : SwitchResult()
    }

    suspend fun encryptedSearch(encryptedQuery: ByteArray): SearchResponse = withContext(Dispatchers.IO) {
        val request = EncryptedSearchRequest.newBuilder()
            .setEncryptedQuery(com.google.protobuf.ByteString.copyFrom(encryptedQuery))
            .build()
        stub!!.encryptedSearch(request)
    }
}

// ============================================================================
// 5. UI IMPLEMENTATION - JETPACK COMPOSE
// ============================================================================

package com.tsm.mobile.ui

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import com.tsm.mobile.HomomorphicSearchPrototype
import com.tsm.mobile.network.TSMNetworkClient
import com.tsm.mobile.ui.theme.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject


sealed class UiState {
    object Unauthenticated : UiState()
    object Authenticated : UiState()
    object Loading : UiState()
    data class Error(val message: String) : UiState()
    data class SearchSuccess(val results: List<String>) : UiState()
}

@HiltViewModel
class MainViewModel @Inject constructor(
    private val networkClient: TSMNetworkClient
) : ViewModel() {

    private val _uiState = MutableStateFlow<UiState>(UiState.Unauthenticated)
    val uiState = _uiState.asStateFlow()

    private val _sessions = MutableStateFlow<List<RemoteSession>>(emptyList())
    val sessions = _sessions.asStateFlow()

    private val _activeSessionId = MutableStateFlow<String?>(null)
    val activeSessionId = _activeSessionId.asStateFlow()

    fun authenticate() {
        // ...
    }

    fun retry() {
        // ...
    }

    fun showSettings() {
        // ...
    }

    fun createBackup() {
        // ...
    }

    fun showActions() {
        // ...
    }

    fun showSecurity() {
        // ...
    }

    fun switchSession(sessionId: String) {
        // ...
    }

    fun search(query: String) {
        viewModelScope.launch {
            try {
                _uiState.value = UiState.Loading
                val searchPrototype = HomomorphicSearchPrototype()
                val encryptedQuery = searchPrototype.generateEncryptedQuery(query.toInt())
                val response = networkClient.encryptedSearch(encryptedQuery.toByteArray())
                _uiState.value = UiState.SearchSuccess(response.sessionLocatorsList)
            } catch (e: Exception) {
                _uiState.value = UiState.Error(e.message ?: "Search failed")
            }
        }
    }
}


@Composable
fun TSMApp() {
    TSMTheme {
        val viewModel: MainViewModel = hiltViewModel()
        val uiState by viewModel.uiState.collectAsStateWithLifecycle()
        
        when (val state = uiState) {
            is UiState.Unauthenticated -> {
                BiometricAuthScreen(
                    onAuthenticate = { viewModel.authenticate() }
                )
            }
            is UiState.Authenticated -> {
                MainScreen(viewModel)
            }
            is UiState.Loading -> {
                LoadingScreen()
            }
            is UiState.Error -> {
                ErrorScreen(
                    message = state.message,
                    onRetry = { viewModel.retry() }
                )
            }
            is UiState.SearchSuccess -> {
                SearchResultsScreen(results = state.results)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(viewModel: MainViewModel) {
    val sessions by viewModel.sessions.collectAsStateWithLifecycle()
    val activeSessionId by viewModel.activeSessionId.collectAsStateWithLifecycle()
    var searchQuery by remember { mutableStateOf("") }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Text(
                        "TSM",
                        style = MaterialTheme.typography.headlineMedium.copy(
                            fontWeight = FontWeight.Bold
                        )
                    )
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                    titleContentColor = MaterialTheme.colorScheme.primary
                ),
                actions = {
                    IconButton(onClick = { viewModel.search(searchQuery) }) {
                        Icon(Icons.Default.Search, contentDescription = "Search")
                    }
                    IconButton(onClick = { viewModel.showSettings() }) {
                        Icon(Icons.Default.Settings, contentDescription = "Settings")
                    }
                }
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = { viewModel.createBackup() },
                icon = { Icon(Icons.Default.Add, contentDescription = null) },
                text = { Text("Backup") },
                containerColor = MaterialTheme.colorScheme.primary
            )
        },
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    selected = true,
                    onClick = { },
                    icon = { Icon(Icons.Default.List, contentDescription = null) },
                    label = { Text("Sessions") }
                )
                NavigationBarItem(
                    selected = false,
                    onClick = { viewModel.showActions() },
                    icon = { Icon(Icons.Default.PlayArrow, contentDescription = null) },
                    label = { Text("Actions") }
                )
                NavigationBarItem(
                    selected = false,
                    onClick = { viewModel.showSecurity() },
                    icon = { Icon(Icons.Default.Security, contentDescription = null) },
                    label = { Text("Security") }
                )
            }
        }
    ) { paddingValues ->
        Column(modifier = Modifier.padding(paddingValues)) {
            TextField(
                value = searchQuery,
                onValueChange = { searchQuery = it },
                label = { Text("Search") },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp)
            )
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize(),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(sessions) { session ->
                    SessionCard(
                        session = session,
                        isActive = session.id == activeSessionId,
                        onClick = { viewModel.switchSession(session.id) }
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SessionCard(
    session: RemoteSession,
    isActive: Boolean,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (isActive) {
                MaterialTheme.colorScheme.primaryContainer
            } else {
                MaterialTheme.colorScheme.surface
            }
        ),
        border = if (isActive) {
            BorderStroke(2.dp, MaterialTheme.colorScheme.primary)
        } else null
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = session.name,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold
                )
                
                if (isActive) {
                    Badge(
                        containerColor = MaterialTheme.colorScheme.primary
                    ) {
                        Text("ACTIVE", modifier = Modifier.padding(horizontal = 8.dp))
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = session.lastUsed,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                
                Text(
                    text = session.sizeFormatted,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            if (session.tags.isNotEmpty()) {
                Spacer(modifier = Modifier.height(8.dp))
                
                Row(
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    session.tags.forEach { tag ->
                        AssistChip(
                            onClick = { },
                            label = { Text(tag, style = MaterialTheme.typography.labelSmall) },
                            modifier = Modifier.height(24.dp)
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun BiometricAuthScreen(onAuthenticate: () -> Unit) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        MaterialTheme.colorScheme.surface,
                        MaterialTheme.colorScheme.surfaceVariant
                    )
                )
            ),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(24.dp)
        ) {
            Icon(
                imageVector = Icons.Default.Fingerprint,
                contentDescription = null,
                modifier = Modifier.size(80.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            
            Text(
                text = "Authentication Required",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.SemiBold
            )
            
            Text(
                text = "Verify your identity to access sessions",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Button(
                onClick = onAuthenticate,
                modifier = Modifier
                    .fillMaxWidth(0.6f)
                    .height(56.dp)
            ) {
                Text("Authenticate", style = MaterialTheme.typography.titleMedium)
            }
        }
    }
}

// ============================================================================
// 6. BACKGROUND SERVICES
// ============================================================================

package com.tsm.mobile.service

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.hilt.work.HiltWorker
import androidx.work.*
import com.tsm.mobile.MainActivity
import com.tsm.mobile.R
import com.tsm.mobile.TSMApplication
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import java.util.concurrent.TimeUnit

@HiltWorker
class SessionMonitorWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val networkClient: TSMNetworkClient,
    private val notificationManager: NotificationManagerCompat
) : CoroutineWorker(context, params) {
    
    override suspend fun doWork(): Result {
        return try {
            // Check server connectivity
            val isConnected = networkClient.checkConnection()
            
            if (!isConnected) {
                showNotification(
                    "Connection Lost",
                    "Unable to connect to TSM desktop server"
                )
            }
            
            // Get current session status
            val status = networkClient.getStatus()
            
            // Check for any alerts
            if (status.hasSecurityAlert) {
                showNotification(
                    "Security Alert",
                    status.alertMessage,
                    NotificationCompat.PRIORITY_HIGH
                )
            }
            
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }
    
    private fun showNotification(
        title: String,
        message: String,
        priority: Int = NotificationCompat.PRIORITY_DEFAULT
    ) {
        val intent = Intent(applicationContext, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            applicationContext,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        
        val notification = NotificationCompat.Builder(
            applicationContext,
            TSMApplication.CHANNEL_SESSION
        )
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(message)
            .setPriority(priority)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()
        
        notificationManager.notify(NOTIFICATION_ID, notification)
    }
    
    companion object {
        private const val NOTIFICATION_ID = 1001
        
        fun schedule(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()
            
            val request = PeriodicWorkRequestBuilder<SessionMonitorWorker>(
                15, TimeUnit.MINUTES
            )
                .setConstraints(constraints)
                .build()
            
            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                "session_monitor",
                ExistingPeriodicWorkPolicy.KEEP,
                request
            )
        }
    }
}

// ============================================================================
// 7. LOCAL STORAGE & STATE MANAGEMENT
// ============================================================================

package com.tsm.mobile.data

import androidx.room.*
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

// Room Database
@Database(
    entities = [SessionEntity::class, EventLogEntity::class],
    version = 1,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class TSMDatabase : RoomDatabase() {
    abstract fun sessionDao(): SessionDao
    abstract fun eventLogDao(): EventLogDao
}

@Entity(tableName = "sessions")
data class SessionEntity(
    @PrimaryKey val id: String,
    val name: String,
    val createdAt: Long,
    val sizeBytes: Long,
    val fileCount: Int,
    val tags: List<String>,
    val isActive: Boolean,
    val lastSyncedAt: Long
)

@Dao
interface SessionDao {
    @Query("SELECT * FROM sessions ORDER BY createdAt DESC")
    fun getAllSessions(): Flow<List<SessionEntity>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSessions(sessions: List<SessionEntity>)
    
    @Query("UPDATE sessions SET isActive = :isActive WHERE id = :id")
    suspend fun updateActiveStatus(id: String, isActive: Boolean)
}

// DataStore for preferences
val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "tsm_prefs")

@Singleton
class PreferencesManager @Inject constructor(
    private val dataStore: DataStore<Preferences>
) {
    companion object {
        val SERVER_HOST = stringPreferencesKey("server_host")
        val SERVER_PORT = intPreferencesKey("server_port")
        val AUTO_LOCK = booleanPreferencesKey("auto_lock")
        val BIOMETRIC_ENABLED = booleanPreferencesKey("biometric_enabled")
        val THEME_MODE = stringPreferencesKey("theme_mode")
    }
    
    val serverHost: Flow<String> = dataStore.data
        .map { it[SERVER_HOST] ?: "192.168.1.100" }
    
    val serverPort: Flow<Int> = dataStore.data
        .map { it[SERVER_PORT] ?: 50051 }
    
    suspend fun updateServerConnection(host: String, port: Int) {
        dataStore.edit { prefs ->
            prefs[SERVER_HOST] = host
            prefs[SERVER_PORT] = port
        }
    }
}

// ============================================================================
// 8. MANIFEST & PERMISSIONS
// ============================================================================

"""
AndroidManifest.xml:

<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">

    <!-- Permissions -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.USE_BIOMETRIC" />
    <uses-permission android:name="android.permission.CAMERA" /> <!-- For QR scanning -->
    <uses-permission android:name="android.permission.VIBRATE" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    
    <!-- Features -->
    <uses-feature android:name="android.hardware.camera" android:required="false" />
    <uses-feature android:name="android.hardware.camera.autofocus" android:required="false" />
    <uses-feature android:name="android.hardware.strongbox_keystore" android:required="false" />

    <application
        android:name=".TSMApplication"
        android:allowBackup="false"
        android:dataExtractionRules="@xml/data_extraction_rules"
        android:fullBackupContent="false"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:networkSecurityConfig="@xml/network_security_config"
        android:supportsRtl="true"
        android:theme="@style/Theme.TSM"
        tools:targetApi="31">
        
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTop"
            android:theme="@style/Theme.TSM">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
        
        <!-- WorkManager initialization -->
        <provider
            android:name="androidx.startup.InitializationProvider"
            android:authorities="${applicationId}.androidx-startup"
            tools:node="remove" />
        
        <!-- File provider for secure file sharing -->
        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>
        
    </application>

</manifest>
"""