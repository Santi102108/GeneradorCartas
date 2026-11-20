# Generador de cartas de cesantías

Aplicación Flask para completar la **plantilla original** `plantilla.docx` y entregar cartas **exclusivamente en PDF**.

## Arquitectura

- `interfaz.py`: interfaz web, vista previa, validaciones y descarga PDF.
- `generador.py`: reemplazo de campos preservando runs de Word, tablas, bordes y configuración de página. Convierte DOCX temporal a PDF sin almacenar cartas permanentemente.
- `utilidades.py`: validación estricta de pesos colombianos, escritura en letras y formatos de fecha.
- `templates/index.html` y `static/style.css`: interfaz responsive.
- `test_generador.py`: pruebas unitarias de importes, formato y rutas web.
- `test_integracion_pdf.py`: verifica cinco PDF generados desde la plantilla real, texto correcto, número de páginas y tamaño del papel.

## PDF

**Sin créditos ni cuota diaria por documento.** La conversión utiliza exclusivamente LibreOffice instalado en la imagen Docker. No hace llamadas a CloudConvert, aunque exista una clave antigua en el entorno. Los PDF se producen localmente y se devuelven como descarga, sin almacenar cartas en el servidor. El límite práctico depende de CPU, RAM, peticiones simultáneas y cuotas del proveedor de alojamiento; no implica capacidad infinita.

Despliegue: imagen `Dockerfile` basada en Python 3.11 con LibreOffice Writer y tipografías sustitutivas. Arranque web mediante Gunicorn dentro del contenedor. Los puntos de entrada `app:app` y `web_app:app` se mantienen por compatibilidad. El formulario nunca expone DOCX, solo archivos PDF.

## Comprobaciones

`python -m unittest discover -p 'test_*.py' -v`

Las pruebas de integración PDF necesitan LibreOffice y `pdftotext`/`pdfinfo` (Poppler). GitHub Actions prueba además la imagen Docker real y solicita cinco PDF por HTTP.

## Privacidad y conservación

La plantilla original no se modifica. Los archivos intermedios se crean en directorios temporales únicos y se eliminan al terminar la solicitud. No se registran datos personales de los formularios. Para evitar incorporar nuevos documentos privados al repositorio, se ignoran `Documentos Generados/` y patrones de cartas exportadas. Los documentos **ya versionados** no se eliminan automáticamente; requieren revisión y autorización antes de cambiar su historial.

## Despliegue Render Docker

Usar `Dockerfile` como runtime `docker`, plan adecuado a las conversiones esperadas. No configurar `CLOUDCONVERT_API_KEY`: el conversor local nunca la utiliza. Conservar el servicio anterior hasta probar el nuevo servicio con una descarga real. Al migrar el dominio, comprobar que PDF y tablas mantienen el formato deseado.
