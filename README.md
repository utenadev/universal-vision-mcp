# Universal Vision MCP 👁️

> **「あなたの AI に、本物の『目』と『首』を。」**

Universal Vision MCP は、あなたのパソコンに繋がったカメラを、AI（Claude など）が直接操作できるようにするためのツールです。
これを使うと、AI はあなたの周りの景色を見たり、ネットワークカメラの首を振って辺りを見渡したりできるようになります。

## 🌟 なにができるの？

![Mock Camera Preview](assets/mock-preview.png)
<br>*(AI がカメラを通じて世界を見ているときのイメージ)*

- **いろんなカメラに対応**: パソコン内蔵のカメラ、USB カメラ、そしてネットワーク上の防犯カメラ（RTSP/ONVIF）まで、AI が同じように扱えます。
- **AI が「自分の体」を理解**: AI は自分が「首を振れるカメラ（PTZ）」なのか「固定されたカメラ」なのかを自分で理解して行動します。
- **自動で見つける**: AI がお家の中のネットワークをスキャンして、新しいカメラを自分で見つけるお手伝いもしてくれます。
- **ライブ表示**: AI に「カメラを見せて」と頼むと、あなたの画面にリアルタイムの映像ウィンドウを表示します。

## 🚀 かんたんな始め方

難しいプログラムのダウンロードや設定は不要です。以下の手順ですぐに始められます。

### 1. [uv](https://docs.astral.sh/uv/) のインストール
まずは、このツールを動かすための軽量な実行環境 `uv` を入れます（たった 1 行です）。

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. MCP クライアントへの登録

#### Claude Desktop (stdio モード)

以下のコマンドを実行してください：

```bash
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp setup --setup-cmd-cd
```

画面に表示された **`mcpServers`** から始まる設定を、Claude Desktop の設定ファイル（`claude_desktop_config.json`）にコピー＆ペーストして Claude を再起動すれば完了です！

#### HTTP モード（SSE / Streamable HTTP 対応クライアント向け）

SSE や Streamable HTTP に対応したクライアント（Claude Code、一部の MCP クライアントなど）では、HTTP サーバーとして起動できます：

```bash
# HTTP サーバーとして起動（デフォルト: 127.0.0.1:8000）
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp run --http

# ポート指定
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp run --http --port 3000
```

**エンドポイント:**
- SSE: `http://<サーバーIP>:8000/sse`
- Streamable HTTP: `http://<サーバーIP>:8000/mcp`

**Claude Code での登録例:**
```bash
claude mcp add universal-vision --transport sse http://<サーバーIP>:8000/sse
```

または設定ファイル（`~/.claude/settings.json`）に直接記述：
```json
{
  "mcpServers": {
    "universal-vision": {
      "url": "http://<サーバーIP>:8000/mcp"
    }
  }
}
```

#### LAN 内での利用（他のマシンからの接続）

同一 LAN 内の他のマシンから接続するには、`--lan` オプションを使用します：

```bash
# LAN モードで起動（0.0.0.0 にバインド）
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp run --http --lan
```

> ⚠️ **重要: LAN 内利用を前提としています**
> LAN モードは認証機能を持たず、`0.0.0.0` にバインドします。
> **信頼できる LAN 内でのみ**使用してください。インターネットに公開しないでください。

#### WSL2 / Windows 間での接続

Windows 側でサーバーを起動し、WSL2 側から接続する場合：

**1. Windows 側でサーバー起動:**
```powershell
# PowerShell で実行（--lan オプションで LAN 接続を許可）
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp run --http --lan
```

**2. Windows 側の IP アドレスを確認（WSL2 内で）:**
```bash
# WSL2 側で実行
cat /etc/resolv.conf | grep nameserver | awk '{print $2}'
```

**3. WSL2 側のクライアントから接続:**
```bash
# 確認したIPアドレスを使用（例: 172.xx.xx.1）
claude mcp add universal-vision --transport sse http://172.xx.xx.1:8000/sse
```

## 🛠️ 便利な機能（困ったときは）

インストールなしで、いつでも以下のコマンドで診断や設定ができます。

```bash
# カメラが正しく認識されているかチェック（診断）
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp doctor --enable-netscan

# ネットワークカメラを追加したり、設定を変更する
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp setup

# テストキャプチャ（画質確認用）
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp test-capture --name mock_eye --count 3
```

## 🆕 新機能（2026-04-11 更新）

### 🌐 HTTP トランスポート対応

SSE (Server-Sent Events) と Streamable HTTP トランスポートをサポートしました。これにより、より多くの MCP クライアントから接続できるようになります。

- **SSE トランスポート**: `/sse` エンドポイント
- **Streamable HTTP トランスポート**: `/mcp` エンドポイント
- **ステートレスモード**: スケーラビリティに優れた JSON レスポンス方式

```bash
# HTTP モードで起動
uv run universal-vision-mcp run --http --port 8000
```

---

## 🆕 新機能（2026-03-07 更新）

### 📸 OSD（オン・スクリーン・ディスプレイ）機能

プレビュー画面に様々な情報を表示できるようになりました。

- **キャプチャ時フラッシュ**: `test-capture` コマンド実行時に緑色のフラッシュと「Now Capturing!!」表示（0.5 秒）
  - ⚠️ **注意**: AI (`see_...` ツール) からのキャプチャではフラッシュは表示されません
- **画質パラメータ表示**: 画面下部に「RES: 1024p | QUAL: 95%」と常時表示
- **Recording 表示**: 記録中に「● REC ...」と経過時間を表示（1 秒点滅）
  - ⚠️ **注意**: 録画開始/停止の MCP ツールは未提供（手動操作のみ）

### 🎚️ リアルタイム画質調整

プレビュー画面のトラックバーで、以下のパラメータをリアルタイム調整可能：

- **解像度**: 512px 〜 1568px（デフォルト：1024px）
- **JPEG 品質**: 50% 〜 98%（デフォルト：95%）

> ⚠️ **注意**: AI への画像送信時は常に 1024px / 95% が使用されます（設定値はAIキャプチャに影響しません）

### 🧪 ベンチマークツール

画像認識の精度を測定するツールを追加：

```bash
# 指の本数認識テスト
uv run python src/universal_vision_mcp/benchmark_recognition.py --task finger_count --iterations 5

# 文字認識テスト
uv run python src/universal_vision_mcp/benchmark_recognition.py --task text_read --iterations 3
```

> ⚠️ **現在このツールはシミュレーターです**: 実際の LLM API 呼び出しは行わず、乱数ベースの結果を返します

### 📋 設定ファイルの拡張

`~/.universal-vision-mcp/config.json` で画質設定を管理：

```json
{
  "cameras": [
    {
      "name": "usb_eye_0",
      "type": "local",
      "index": 0,
      "target_height": 1024,
      "jpeg_quality": 95
    }
  ],
  "default_target_height": 1024,
  "default_jpeg_quality": 95
}
```

---

## 👨‍💻 開発者の方へ (For Developers)

自分で改造したり、ソースコードを読みたい方向けのステップです。

### セットアップ
```bash
git clone https://github.com/utenadev/universal-vision-mcp
cd universal-vision-mcp
uv sync
```

### 実行・診断
```bash
# stdio モード（デフォルト）
uv run universal-vision-mcp doctor
uv run universal-vision-mcp run

# HTTP モード（SSE + Streamable HTTP）
uv run universal-vision-mcp run --http --port 8000
```

## 🧠 技術スタック & 設計思想

ここからは技術的なお話です。

- **Python 3.11+ / MCP Python SDK**: Model Context Protocol 準拠。
- **複数トランスポート対応**: stdio / SSE / Streamable HTTP をサポート。
- **OpenCV**: 映像キャプチャとプレビュー表示。
- **ONVIF**: ネットワークカメラの PTZ 制御。
- **S 式による自己記述**: LLM に対して、以下のような身体記述をツール説明に注入します。
  ```lisp
  (part :id garden_cam :type network :tool see_garden_cam :desc "...")
  ```
  これにより、AI は単なる関数呼び出しではなく「自分には PTZ 対応の目があり、それを使って周囲を見渡せる」という**身体感覚（Embodiment）**を持って行動します。

## ❤️ 謝辞 (Acknowledgments)

このプロジェクトは、**kmizu (lifemate-ai)** 氏による先駆的な仕事（`embodied-claude`, `familiar-ai`）に深くインスパイアされています。AI に実体を持たせるという素晴らしい「アソビ」を提案してくださったことに、最大の敬意と感謝を捧げます。

## 📜 ライセンス
MIT License
