I have updated the android_build_guide.md with even more detailed instructions, assuming no prior knowledge of Android development.

Here is the new content of the file:

# The Ultimate Guide to Building the TSM Android Client

Welcome! This guide provides a comprehensive, step-by-step walkthrough for building the Android client for the Telegram Session Manager (TSM) application. This guide is designed for everyone, especially those who are new to Android development. We've simplified the process by using Docker, a tool that creates a self-contained, virtual environment for building software. This means you don't have to worry about installing and configuring complex development tools on your computer.

## Table of Contents

1.  [What is Docker and Why Do We Use It?](#what-is-docker-and-why-do-we-use-it)
2.  [Prerequisites: Installing Docker](#prerequisites-installing-docker)
3.  [The Build Process: A High-Level Overview](#the-build-process-a-high-level-overview)
4.  [Step-by-Step Build Instructions](#step-by-step-build-instructions)
5.  [Understanding the Magic: What Happens Under the Hood](#understanding-the-magic-what-happens-under-the-hood)
6.  [Finding Your Golden Ticket: Locating the APK](#finding-your-golden-ticket-locating-the-apk)
7.  [When Things Go Wrong: Troubleshooting](#when-things-go-wrong-troubleshooting)

## What is Docker and Why Do We Use It?

Imagine you're trying to bake a cake. You need a specific type of oven, a specific set of ingredients, and a specific set of instructions. If any of these are slightly off, your cake might not turn out right.

Docker is like a magical, portable kitchen that you can set up anywhere. It has the perfect oven, all the right ingredients, and the recipe is built right in. When you want to bake a cake, you just tell Docker to set up the kitchen and bake it for you. You get a perfect cake every time, and you don't have to worry about cluttering your own kitchen with tools you might only use once.

In our case, the "cake" is the TSM Android application. The "kitchen" is the build environment, and the "ingredients" are the specific versions of the Java Development Kit (JDK), the Android SDK, and other tools. By using Docker, we ensure that everyone is using the exact same "kitchen" to build the app, which eliminates a whole class of problems.

## Prerequisites: Installing Docker

Before you can build the TSM Android client, you need to install Docker on your computer.

1.  **Download Docker Desktop:** Go to the official Docker website and download Docker Desktop for your operating system: [https://www.docker.com/get-started](https://www.docker.com/get-started)
2.  **Install Docker Desktop:** Follow the installation instructions for your operating system. This will likely involve running an installer and following the on-screen prompts.
3.  **Start Docker Desktop:** Once Docker is installed, start the Docker Desktop application. You should see a whale icon in your system tray or menu bar.
4.  **Verify the Installation:** Open a terminal or command prompt and run the following command:
    ```bash
    docker --version
    ```
    You should see the Docker version information printed to the console. If you get an error, it's likely that the Docker daemon is not running. Please make sure that Docker Desktop is running and try the command again.

## The Build Process: A High-Level Overview

The entire build process is automated by a single script. When you run this script, it will:

1.  **Build a custom Docker image:** This image is a self-contained environment with all the tools needed to build the Android app.
2.  **Start a Docker container:** This is a running instance of the Docker image.
3.  **Run the Gradle build:** Inside the container, the script will run the Gradle build, which will compile the code and package it into an APK.

## Step-by-Step Build Instructions

1.  **Open a Terminal or Command Prompt:**
    *   **On macOS:** You can find the Terminal application in `/Applications/Utilities/`.
    *   **On Windows:** You can use the Command Prompt or PowerShell, which can be found in the Start Menu.
    *   **On Linux:** You can usually find the terminal in your applications menu.

2.  **Navigate to the Android Project Directory:**
    In your terminal, use the `cd` command to change your current directory to the `mobile/android` directory within the TSM project. The exact command will depend on where you have saved the project on your computer. For example:
    ```bash
    cd /path/to/your/project/mobile/android
    ```

3.  **Make the Build Script Executable:**
    The `docker-build.sh` script needs to have execute permissions to run. Grant these permissions with the following command:
    ```bash
    chmod +x docker-build.sh
    ```
    You only need to run this command once.

4.  **Run the Build Script:**
    Now, you can execute the build script:
    ```bash
    ./docker-build.sh
    ```
    You will see a lot of text scrolling by in your terminal. This is normal! The script is building the Docker image and then building the Android app. This process can take several minutes, especially the first time you run it, as it needs to download the base Docker image and all the necessary dependencies.

## Understanding the Magic: What Happens Under the Hood

The `docker-build.sh` script is the heart of the build process. Here's a more detailed look at what it's doing:

*   **`docker build -t tsm-android-builder -f Dockerfile.build .`**
    *   This command tells Docker to build a new image.
    *   The `-t tsm-android-builder` flag gives the image a name, so we can refer to it later.
    *   The `-f Dockerfile.build` flag tells Docker to use the `Dockerfile.build` file for the build instructions.
    *   The `.` at the end tells Docker to use the current directory as the build context.

*   **`docker run -v $(pwd):/workspace tsm-android-builder ./gradlew assembleRelease`**
    *   This command tells Docker to run a new container from the `tsm-android-builder` image we just created.
    *   The `-v $(pwd):/workspace` flag mounts the current directory on your computer to the `/workspace` directory inside the container. This is how the container gets access to the source code.
    *   The `./gradlew assembleRelease` part is the command that is run inside the container. This is the command that actually builds the Android app.

## Finding Your Golden Ticket: Locating the APK

Once the build script has finished running, you will have a brand new APK file ready to be installed on an Android device. You can find this file in the following directory:

`mobile/android/app/build/outputs/apk/release/`

The file will be named `app-release.apk`.

## When Things Go Wrong: Troubleshooting

*   **"Cannot connect to the Docker daemon"**: This error means that the Docker service is not running on your machine. Please make sure that you have started Docker Desktop and that it is running correctly.
*   **"permission denied"**: If you see this error when you try to run the `./docker-build.sh` script, it means that the script does not have execute permissions. Please run the `chmod +x docker-build.sh` command again.
*   **Network errors:** The build process requires an internet connection to download the base Docker image, Android SDK components, and Gradle dependencies. If you see errors related to network timeouts or "host not found", please check your internet connection. If you are on a corporate network with a firewall or proxy, you may need to configure Docker to use it. Please refer to the official Docker documentation for more information.
