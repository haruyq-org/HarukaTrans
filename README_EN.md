# Haruka Trans (Transcriber / Translator)

Haruka Trans is a real-time transcription and translation application specifically developed for VRChat. This app enables smooth communication across multiple languages.

<img src="./assets/Screenshot 2026-03-31 140334.png" width="600" height="400">

## Installation

1. Download `HarukaTrans.zip` from the [**latest release**](https://github.com/haruyq-org/HarukaTrans/releases/latest) and extract the files.
2. Execute `HarukaTrans.exe` included in the folder.
3. Once the application window appears, the installation is complete.

## Usage

Check the various settings from the settings button on the right side of the header, and click the Start button to begin voice recognition.
At this time, if the translation icon located next to the settings button is green, the text will be translated automatically.

Starting from v0.1.8, you can now enter text in the left area.
Entering a sentence and pressing the Enter key will perform the same action as when voice recognition is used.

## Microphone

The application uses the microphone currently set as the **Windows Default**. 
If the application does not detect your voice, please verify your microphone settings in `Settings -> System -> Sound`.

## Settings

| Parameter      | Value / Example    | Description                                      |
| :------------- | :----------------- | :----------------------------------------------- |
| BASE_URL       | http://example.com | Vox-Box API URL                                  |
| STT_ENGINE     | edgestt / voxbox   | STT engine to be used                            |
| SOURCE_LANG    | ja-JP              | Input source language code                       |
| USE_VAD        | true               | Enable or disable Voice Activity Detection (VAD) |
| VAD_THRESHOLD  | 0.5                | Minimum detection threshold for VAD              |
| VAD_THREADS    | 1                  | Number of threads used for VAD processing        |
| USE_TRANSLATE  | false              | Enable or disable translation                    |
| TRANSLATOR     | google / deepl / gemini | Translation engine to be used               |
| API_KEY        | Your_API_Key       | API key for the external translator service      |
| TARGET_LANG    | en                 | Language code for the translation output         |
| LOG_LEVEL      | INFO               | Level of logging output                          |

### Notes
* If you set `STT_ENGINE` to `voxbox`, you must set up the Vox-Box server separately.
* If a `TRANSLATOR` other than `google` is selected, you must provide a valid `API_KEY`.

## Vox-Box

Depending on the model used, Vox-Box can provide higher accuracy than EdgeSTT. 
In this project, we have confirmed that `Faster-whisper-large-v3` works correctly.

### Setup
Please refer to the [**Official README**](https://github.com/gpustack/vox-box?tab=readme-ov-file#installation) for installation instructions.
We recommend using a separate PC with a dedicated GPU as the API provider.

## Translation Engines

The app supports `Google Translate`, `DeepL Translator`, and `Gemini`.
No additional setup is required if you choose `Google Translate`.

### Setup Instructions

#### DeepL
1. Create a DeepL account via [**this link**](https://www.deepl.com/en/signup?cta=checkout&is_api=true).
2. Navigate to the [DeepL API page](https://www.deepl.com/en/pro-api) and click **"Sign up for free"** under the Free plan.
3. Complete the registration by entering the required information.
4. Access [Your Account Keys](https://www.deepl.com/en/your-account/keys) and click **"Create key"**.
5. Paste the API key into the `Translator API Key` field in the app settings and ensure the `Translator` is set to `DeepL`.

#### Gemini
1. Log in to [**Google AI Studio**](https://aistudio.google.com/).
2. Click **"Get API Key"** on the bottom left of the sidebar.
3. Click **"Create API Key"** at the top right.
4. Name your key, click **"Create Key"**, and copy the generated key.
5. Paste the API key into the `Translator API Key` field in the app settings and ensure the `Translator` is set to `Gemini`.

## Execution (From Source)

Python is required to run the application. 
We have confirmed compatibility with **Python 3.10.0**.

```bash
git clone https://github.com/haruyq-org/HarukaTrans.git
cd HarukaTrans

.\setup_win.bat
.\.venv\Scripts\activate

python main.py
```

## Build

```bash
git clone https://github.com/haruyq-org/HarukaTrans.git
cd HarukaTrans

.\setup_win.bat
.\.venv\Scripts\activate

pip install pyinstaller

mkdir vad
cd vad
curl -O https://raw.githubusercontent.com/snakers4/silero-vad/refs/heads/master/src/silero_vad/data/silero_vad.onnx

.\build.bat
```

## License

This project is published under the [MIT License](./LICENSE).