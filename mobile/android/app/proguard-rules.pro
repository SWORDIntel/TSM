# Add project specific ProGuard rules here.
# By default, the flags in this file are appended to flags specified
# in C:\Users\Jules\AppData\Local\Android\sdk\tools\proguard\proguard-android-optimize.txt
# You can edit the include path and order by changing the proguardFiles
# directive in build.gradle.
#
# For more details, see
#   http://developer.android.com/guide/developing/tools/proguard.html

# gRPC
-keepclassmembers class * extends io.grpc.stub.AbstractStub {
    public static final ** SERVICE_NAME;
}
-keepclassmembers class * extends com.google.protobuf.GeneratedMessageLite {
    public static <init>(...);
}
-keep public class * extends com.google.protobuf.GeneratedMessageLite {}

# Tink
-keepclassmembers class com.google.crypto.tink.** { *; }
-dontwarn com.google.crypto.tink.**

# Protobuf
-keep public class com.google.protobuf.** { *; }
-dontwarn com.google.protobuf.**
-keepclassmembers class ** extends com.google.protobuf.GeneratedMessageLite {
    <fields>;
}
