# Haruka Trans(criber / lator)

[English](./README_EN.md)

Haruka Transは、VRChat向けに開発されたリアルタイム文字起こし・翻訳アプリです。  
このアプリでは、様々な言語間で円滑なコミュニケーションを可能にします。

<img src="./assets/Screenshot 2026-03-31 140334.png" width="600" height="400">

## インストール

[**最新のリリース**](https://github.com/haruyq-org/HarukaTrans/releases/latest)から`HarukaTrans.zip`をダウンロードした後、展開します。  
同梱している`HarukaTrans.exe`を実行し、正しくアプリケーションが表示されれば成功です。

## マイク

このアプリは、Windowsにデフォルトとして設定されているマイクを使用します。  
音声が検出されない場合は、`設定 -> システム -> サウンド`から使用するマイクを選択してください。

## 設定

| 項目           | 内容                | 説明                       |
|:---------------|:-------------------|:---------------------------|
| BASE_URL       | http://example.com      | Vox-Box APIの接続先URL |
| STT_ENGINE     | edgestt / voxbox        | 使用するSTTエンジン |
| SOURCE_LANG    | ja-JP                   | 音声入力の言語コード |
| USE_VAD        | true                    | VADを有効化するか |
| VAD_THRESHOLD  | 0.5                     | VADの判定しきい値 |
| VAD_THREADS    | 1                       | VAD処理に使うスレッド数 |
| USE_TRANSLATE  | false                   | 翻訳機能を有効化するか |
| TRANSLATOR     | google / deepl / gemini | 使用する翻訳エンジン |
| API_KEY        | APIKey                  | 外部翻訳APIのキー |
| TARGET_LANG    | en                      | 翻訳先の言語コード |
| LOG_LEVEL      | INFO                    | ログ出力レベル |

### 注意点

* `STT_ENGINE`で`voxbox`を使用する場合は、別途セットアップが必要です。
* `TRANSLATOR`が`google`以外の場合は、`API_KEY`の設定が必要です。

## Vox-Box

使用するモデルによって差異はありますが、EdgeSTTよりも良い結果が得られることがあります。  
このプロジェクトでは、`Faster-whisper-large-v3`にて動作を確認しています。

### インストール

[**公式のREADME**](https://github.com/gpustack/vox-box?tab=readme-ov-file#installation)を参照して下さい。  
メイン機とは別で、ある程度のGPUが搭載されているマシンの使用を推奨します。

## 翻訳エンジン

`Google翻訳` `DeepL翻訳` `Gemini`をサポートしています。  
Google翻訳を使用する場合、下記のセットアップは不要です。  

### セットアップ

#### DeepL

[**こちらのリンク**](https://www.deepl.com/ja/signup?cta=checkout&is_api=true)から、DeepLのアカウントを作成します。  
その後、 https://www.deepl.com/ja/pro-api にアクセスし、**無料で始める**から**無料で登録**を押下します。  
遷移後の画面で情報を入力し、APIの登録を完了します。  

https://www.deepl.com/ja/your-account/keys にアクセスした後、**キーを作成**を押下し、名前(任意)を入力すると、APIキーが作成されます。  
作成したAPIキーを設定画面内の`Translator API Key`に張り付け、`Translator`が`DeepL`に設定されていることを確認したら完了です。

#### Gemini

[**Google AI Studio**](https://aistudio.google.com/)にログインします。  

画面左下の、**Get API Key**を押下し、画面右上の**APIキーを作成**を押下します。  
キー名(任意)を指定し、**キーを作成**を押下するとAPIキーが作成されます。  
作成したAPIキーを設定画面内の`Translator API Key`に張り付け、`Translator`が`Gemini`に設定されていることを確認したら完了です。

## 実行

Pythonがインストールされている必要があります。  
実際に動作を確認しているバージョンは**3.10.0**です。

```bash
git clone https://github.com/haruyq-org/HarukaTrans.git
cd HarukaTrans

.\setup_win.bat

.\.venv\Scripts\activate

python main.py
```

## ビルド

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

## ライセンス

このプロジェクトは[MIT License](./LICENSE)で公開されています。
