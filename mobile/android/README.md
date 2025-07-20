# TSM Android Application

This is the Android client for the Telegram Session Manager (TSM).

## Architecture

The application follows the MVVM (Model-View-ViewModel) architecture pattern.

*   **Model**: The data layer, consisting of the Room database, repositories, and network services.
*   **View**: The UI layer, built with Jetpack Compose.
*   **ViewModel**: The logic layer, which exposes data to the UI and handles user interactions.

## Modules

*   **Network**: Handles communication with the TSM server using gRPC.
*   **UI**: Contains all the Jetpack Compose screens and UI components.
*   **Data**: Manages the application's data, including the Room database and repositories.
*   **Security**: Handles cryptographic operations using Tink.

## Build Instructions

Once the Android SDK is available, you can build and run the project using the following steps:

1.  Open the project in Android Studio.
2.  Connect a device or start an emulator.
3.  Click the "Run" button.

## ProGuard / R8

The project is configured to use ProGuard for code shrinking and obfuscation in release builds. The rules are defined in `app/proguard-rules.pro`.
