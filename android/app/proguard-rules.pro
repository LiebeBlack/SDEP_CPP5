# Reglas de ofuscación para la versión de distribución.

# Retrofit y sus interfaces anotadas
-keepattributes Signature, InnerClasses, EnclosingMethod, AnnotationDefault
-keepattributes RuntimeVisibleAnnotations, RuntimeVisibleParameterAnnotations
-keep,allowobfuscation,allowshrinking interface retrofit2.Call
-keep,allowobfuscation,allowshrinking class retrofit2.Response
-keep,allowobfuscation,allowshrinking class kotlin.coroutines.Continuation

# Kotlinx Serialization: los DTO se generan con el plugin, pero sus
# serializadores deben conservarse al ofuscar.
-keepclassmembers class kotlinx.serialization.json.** { *; }
-keep,includedescriptorclasses class ve.edu.sdep.movil.**$$serializer { *; }
-keepclassmembers class ve.edu.sdep.movil.** {
    *** Companion;
}
-keepclasseswithmembers class ve.edu.sdep.movil.** {
    kotlinx.serialization.KSerializer serializer(...);
}

# Room no necesita reglas adicionales, pero las entidades se conservan por
# claridad al leer un informe de fallos.
-keep class ve.edu.sdep.movil.datos.local.entidad.** { *; }

# Anotaciones de Error Prone que el cifrado de Android (Tink, usado por
# ``EncryptedSharedPreferences``) referencia con ámbito de compilación y que
# no existen en tiempo de ejecución. Sin esta regla, R8 detenía la compilación
# del APK de release y la versión nunca se podía publicar. Son solo
# anotaciones: no faltan clases que la aplicación necesite de verdad.
-dontwarn com.google.errorprone.annotations.**
