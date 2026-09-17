# Pasar Audio a Texto con Whisper Local

Aplicacion web local para convertir archivos de audio a texto usando
[OpenAI Whisper](https://github.com/openai/whisper). El proyecto usa Flask para
mostrar una interfaz en el navegador y ejecuta Whisper en la computadora, sin
subir los audios a un servicio externo.

## Que hace

- Permite subir audios desde el navegador.
- Acepta archivos `.mp3`, `.wav`, `.m4a`, `.ogg` y `.flac`.
- Transcribe el audio con el modelo Whisper `small`.
- Detecta idioma automaticamente o permite escoger `es`, `en`, `pt` o `fr`.
- Muestra progreso visual mientras procesa.
- Permite copiar el texto generado.
- Elimina el archivo temporal despues de transcribirlo.

## Estructura del proyecto

```text
Pasar audio a texto/
|-- app.py
|-- requirements.txt
|-- templates/
|   `-- index.html
|-- uploads/
`-- venv/
```

Archivos principales:

- `app.py`: servidor Flask, carga el modelo Whisper y maneja las rutas.
- `templates/index.html`: interfaz web.
- `requirements.txt`: dependencias principales.
- `uploads/`: carpeta temporal donde se guardan audios mientras se procesan.
- `venv/`: entorno virtual local de Python.

## Requisitos

- Windows.
- Python instalado.
- FFmpeg instalado y disponible en el `PATH`.
- Conexion a internet la primera vez que Whisper descargue el modelo.

El repositorio oficial de Whisper indica que se instala con:

```bash
pip install -U openai-whisper
```

Tambien requiere FFmpeg. En Windows se puede instalar con Chocolatey o Scoop:

```powershell
choco install ffmpeg
```

o:

```powershell
scoop install ffmpeg
```

En esta maquina ya se verifico:

- Python del entorno actual: `Python 3.14.2`
- Whisper instalado: `openai-whisper==20250625`
- Torch instalado: `torch==2.12.0+cpu`
- CUDA detectado: `False`, por ahora corre en CPU.
- FFmpeg instalado: `ffmpeg 8.1.1`

Nota: Whisper oficialmente espera compatibilidad principalmente con Python
3.8-3.11 y versiones recientes de PyTorch. Aunque este entorno actual con
Python 3.14 esta funcionando, para una instalacion limpia suele ser mas seguro
usar Python 3.11.

## Instalacion desde cero

Abre PowerShell y entra a la carpeta del proyecto:

```powershell
cd "C:\Users\Jean Pierre\Desktop\Pasar audio a texto"
```

Crea un entorno virtual:

```powershell
python -m venv venv
```

Activa el entorno virtual:

```powershell
.\venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activacion, ejecuta esto una vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Luego vuelve a activar:

```powershell
.\venv\Scripts\Activate.ps1
```

Actualiza `pip`:

```powershell
python -m pip install --upgrade pip
```

Instala las dependencias:

```powershell
pip install -r requirements.txt
```

Si Whisper falla al instalar, instala desde el repo oficial:

```powershell
pip install -U openai-whisper
```

Si aparece un error relacionado con Rust o `setuptools_rust`, instala:

```powershell
pip install setuptools-rust
```

## Como ejecutar la app

Desde la carpeta del proyecto, con el entorno virtual activo:

```powershell
python app.py
```

Cuando Flask arranque, abre en el navegador:

```text
http://127.0.0.1:5000
```

La primera ejecucion puede tardar porque Whisper descarga el modelo `small`.
Despues de descargado, queda en cache y los siguientes arranques son mas
rapidos.

## Uso

1. Abre `http://127.0.0.1:5000`.
2. Selecciona un archivo de audio.
3. Escoge idioma o deja deteccion automatica.
4. Pulsa `Iniciar transcripcion`.
5. Espera a que el progreso llegue al 100%.
6. Copia el texto generado si lo necesitas.

## Configuracion importante

En `app.py` el modelo se define aqui:

```python
MODEL_NAME = "small"
```

Puedes cambiarlo por otro modelo de Whisper:

```python
MODEL_NAME = "tiny"
MODEL_NAME = "base"
MODEL_NAME = "small"
MODEL_NAME = "medium"
MODEL_NAME = "large"
MODEL_NAME = "turbo"
```

Guia rapida:

- `tiny`: mas rapido, menos preciso.
- `base`: ligero y aceptable para pruebas.
- `small`: buen equilibrio para este proyecto.
- `medium`: mas preciso, mas lento.
- `large`: mas pesado, mejor calidad.
- `turbo`: rapido y moderno para transcripcion.

En CPU, `small` puede tardar en audios largos. Si la computadora tiene GPU
NVIDIA con CUDA bien configurado, el codigo intenta usarla automaticamente:

```python
device = "cuda" if torch.cuda.is_available() else "cpu"
```

## Dependencias

El archivo `requirements.txt` actual contiene:

```text
flask
openai-whisper
torch
```

Para congelar las versiones exactas del entorno actual:

```powershell
pip freeze > requirements-lock.txt
```

## Problemas comunes

### `ffmpeg` no se reconoce como comando

Instala FFmpeg y confirma que funciona:

```powershell
ffmpeg -version
```

Si no responde, falta agregar FFmpeg al `PATH`.

### La app tarda mucho al iniciar

Es normal la primera vez porque Whisper descarga el modelo. Tambien puede
tardar si se usa un modelo grande.

### La transcripcion tarda demasiado

Cambia el modelo en `app.py`:

```python
MODEL_NAME = "base"
```

o:

```python
MODEL_NAME = "tiny"
```

### El audio queda en `uploads/`

El codigo intenta borrar el archivo al terminar:

```python
os.remove(filepath)
```

Si la app se cierra a mitad del proceso, pueden quedar archivos temporales en
`uploads/`. Se pueden borrar manualmente si ya no hacen falta.

### Caracteres raros en algunos textos

Si ves textos con caracteres raros en lugar de tildes, probablemente algun
archivo se abrio o se guardo con una codificacion incorrecta. Guarda los
archivos como UTF-8.

## Arquitectura

Flujo principal:

```text
Navegador
  |
  v
Flask recibe el archivo en /start
  |
  v
Guarda audio temporal en uploads/
  |
  v
Crea una tarea con UUID
  |
  v
Ejecuta Whisper en un thread separado
  |
  v
El navegador consulta /progress/<task_id>
  |
  v
Cuando termina, muestra el texto transcrito
```

Rutas:

- `GET /`: carga la interfaz web.
- `POST /start`: recibe el audio e inicia la transcripcion.
- `GET /progress/<task_id>`: devuelve progreso, estado, errores y resultado.

## Fuente base

La arquitectura de transcripcion usa OpenAI Whisper:

- Repositorio oficial: https://github.com/openai/whisper
- Licencia de Whisper: MIT
