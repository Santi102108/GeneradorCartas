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

Se utiliza CloudConvert cuando está configurada la variable de entorno `CLOUDCONVERT_API_KEY`. Si no está presente, se usa LibreOffice instalado en el sistema (`LIBREOFFICE_BIN`, opcional). Si no hay ningún motor disponible, se devuelve un error explícito: no se entregan documentos incompletos.

Arranque web con Gunicorn: `gunicorn interfaz:app --bind 0.0.0.0:$PORT`. Los puntos de entrada `app:app` y `web_app:app` se mantienen por compatibilidad. El formulario nunca expone DOCX, solo archivos PDF.

## Comprobaciones

`python -m unittest discover -p 'test_*.py' -v`

Las pruebas de integración PDF necesitan LibreOffice y `pdftotext`/`pdfinfo` (Poppler). GitHub Actions instala estos programas en el entorno de pruebas.

## Privacidad y conservación

La plantilla original no se modifica. Los archivos intermedios se crean en directorios temporales únicos y se eliminan al terminar la solicitud. No se registran datos personales de los formularios. Para evitar incorporar nuevos documentos privados al repositorio, se ignoran `Documentos Generados/` y patrones de cartas exportadas. Los documentos **ya versionados** no se eliminan automáticamente; requieren revisión y autorización antes de cambiar su historial.
