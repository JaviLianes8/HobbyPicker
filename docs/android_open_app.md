# Abrir una app de Android si está instalada

Este ejemplo en Kotlin muestra cómo verificar si una aplicación está instalada en el dispositivo y abrirla directamente. Si la aplicación no está instalada, redirige al usuario a la tienda para descargarla.

```kotlin
val packageName = "com.example.juego"

val isInstalled = try {
    context.packageManager.getPackageInfo(packageName, 0)
    true
} catch (_: PackageManager.NameNotFoundException) {
    false
}

if (isInstalled) {
    // La app está instalada, la abrimos
    val launchIntent = context.packageManager.getLaunchIntentForPackage(packageName)
    if (launchIntent != null) {
        context.startActivity(launchIntent)
    } else {
        // Si no se encuentra el intent de lanzamiento, notificamos al usuario
        Toast.makeText(context, "No se puede abrir la app", Toast.LENGTH_SHORT).show()
    }
} else {
    // La app no está instalada, redirigimos a la tienda
    val playStoreIntent = Intent(Intent.ACTION_VIEW).apply {
        data = Uri.parse("market://details?id=$packageName")
        flags = Intent.FLAG_ACTIVITY_NEW_TASK
    }
    context.startActivity(playStoreIntent)
}
```

Este flujo se puede integrar en un botón para ofrecer una experiencia fluida al usuario: si el juego ya está instalado, se abre automáticamente; de lo contrario, se lleva a la tienda para su instalación.
