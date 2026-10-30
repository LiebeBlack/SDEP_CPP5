plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.serialization")
    id("com.google.devtools.ksp")
    id("com.google.dagger.hilt.android")
}

// La versión del teléfono sale del VERSION del producto: antes estaba fija en
// 1.0.0 y cada release obligaba a recordar cambiarla aquí a mano.
val versionProducto: String =
    rootProject.file("../VERSION").takeIf { it.isFile }?.readText()?.trim()
        ?.takeIf { it.isNotEmpty() } ?: "3.0.1"

/** 3.0.1 → 30001: el código de versión sube solo con cada release. */
val codigoVersion: Int = versionProducto.split(".").let { partes ->
    partes[0].toInt() * 10_000 +
        (partes.getOrNull(1)?.toInt() ?: 0) * 100 +
        (partes.getOrNull(2)?.toInt() ?: 0)
}

android {
    namespace = "ve.edu.sdep.movil"
    compileSdk = 34

    defaultConfig {
        applicationId = "ve.edu.sdep.movil"
        minSdk = 26
        targetSdk = 34
        versionCode = codigoVersion
        versionName = versionProducto
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        resourceConfigurations += listOf("es")
    }

    // Firma opcional para distribuir: el almacén y sus contraseñas se pasan por
    // variables de entorno (CI o el equipo del responsable) y nunca se copian
    // al repositorio. Sin ellas, el APK de release se genera sin firmar, que es
    // lo que basta para validar R8 y la ofuscación en cada integración.
    signingConfigs {
        val almacen = System.getenv("SDEP_KEYSTORE")
            ?.takeIf { it.isNotBlank() }
            ?.let { file(it) }
            ?.takeIf { it.exists() }
        if (almacen != null) {
            create("release") {
                storeFile = almacen
                storePassword = System.getenv("SDEP_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("SDEP_KEY_ALIAS")
                keyPassword = System.getenv("SDEP_KEY_PASSWORD")
            }
        }
    }

    val firmaRelease = signingConfigs.findByName("release")

    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            firmaRelease?.let { signingConfig = it }
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
        freeCompilerArgs += listOf("-opt-in=kotlin.RequiresOptIn")
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.14"
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    // Base y ciclo de vida
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.4")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.4")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.4")
    implementation("androidx.activity:activity-compose:1.9.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.fragment:fragment-ktx:1.8.2")

    // Compose y Material 3
    implementation(platform("androidx.compose:compose-bom:2024.06.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.navigation:navigation-compose:2.7.7")

    // Inyección de dependencias
    implementation("com.google.dagger:hilt-android:2.51.1")
    ksp("com.google.dagger:hilt-android-compiler:2.51.1")
    implementation("androidx.hilt:hilt-navigation-compose:1.2.0")
    implementation("androidx.hilt:hilt-work:1.2.0")
    ksp("androidx.hilt:hilt-compiler:1.2.0")

    // Trabajo en segundo plano
    implementation("androidx.work:work-runtime-ktx:2.9.0")

    // Persistencia local
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")

    // Red y serialización
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.jakewharton.retrofit:retrofit2-kotlinx-serialization-converter:1.0.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.3")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    // Seguridad: bóveda cifrada y biometría
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
    implementation("androidx.biometric:biometric:1.2.0-alpha05")

    // Pruebas
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.8.1")
    testImplementation("com.google.truth:truth:1.4.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
    androidTestImplementation("androidx.room:room-testing:2.6.1")

    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
