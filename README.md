# Yu-Gi-Oh! DB 画像一括ダウンローダ（Windows）

Yu-Gi-Oh! DB のカード詳細ページ（cid）一覧からカード画像をダウンロードします。

## 特徴
- cid 一覧ファイルを読み込み、画像を自動保存
- 既存ファイルのスキップ、リトライ、アクセス間隔（sleep）に対応
- `Content-Type: application/octet-stream` でも実体が画像なら自動判定して保存

## 動作環境
- Windows 10 / 11
- Python 3.10 以上（3.12/3.13 でも可）
- PowerShell または コマンドプロンプト

## ファイル構成例
```
yugioh-image-downloader/
├─ download_yugioh_images.py
├─ cids.txt
└─ images/              # 実行後に作成される
```

## 事前準備（Python をまだ入れていない場合）
1. **Python のインストール**
   - Microsoft Store で「Python 3.x」をインストール
   - または [python.org](https://www.python.org/) の Windows Installer を利用
   - python.org 版は「**Add python.exe to PATH**」に必ずチェックを入れてください。
2. **動作確認**
   ```powershell
   python --version
   # もしくは
   py -3 --version
   ```
   `Python 3.x.x` が表示されれば準備完了です。

## 仮想環境の作成（推奨）
1. 作業フォルダへ移動します。
   ```powershell
   cd C:\path\to\yugioh-image-downloader
   ```
2. venv を作成します。
   ```powershell
   python -m venv .venv
   ```
3. venv を有効化します。
   ```powershell
   # PowerShell
   .\.venv\Scripts\Activate.ps1

   # コマンドプロンプト
   .\.venv\Scripts\activate.bat
   ```
   有効化されるとプロンプト先頭に `(.venv)` が表示されます。
4. 依存関係をインストールします。
   ```powershell
   python -m pip install --upgrade pip
   pip install requests beautifulsoup4 lxml
   ```

### PowerShell の実行ポリシーでブロックされた場合
`running scripts is disabled on this system` が表示されたら、PowerShell で次を実行して CurrentUser のみスクリプトを許可します（管理者権限不要）。
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
その後、再度 `Activate.ps1` を実行してください。

## cid 一覧ファイルの準備
`cids.txt` を作成し、ダウンロードしたい cid を列挙します。
- 1 行 1 cid でも空白区切りでも可
- `#` 始まりの行はコメントとして無視されます

例:
```
# sample
12424
9074
10522
6114
```

## 使い方
### 基本
```powershell
python download_yugioh_images.py --cid-file cids.txt --skip-existing
```
既存ファイルがある場合はスキップします。

### 負荷を抑える設定（推奨）
```powershell
python download_yugioh_images.py --cid-file cids.txt --skip-existing --sleep 0.8 --retries 4
```
アクセス間隔とリトライ回数を増やしてサーバー負荷を軽減します。

### 主なオプション
| オプション | 説明 | デフォルト |
| --- | --- | --- |
| `--cid-file <path>` | cid 一覧ファイル（必須） | なし |
| `--outdir <dir>` | 出力ディレクトリ | `images` |
| `--locale <en|ja|...>` | request_locale | `en` |
| `--sleep <sec>` | cid ごとの待機秒 | `0.4` |
| `--retries <n>` | 失敗時リトライ回数 | `2` |
| `--timeout <sec>` | HTTP タイムアウト | `30` |
| `--skip-existing` | `images\\<cid>.*` が存在する場合スキップ | - |

## 出力仕様
- 出力先: `images/`
- ファイル名: `<cid>.<ext>`（例: `images\12424.png`）
- 拡張子は実体に合わせて自動判定（`.png`/`.jpg`/`.webp`/`.gif` など）

## トラブルシューティング
- **python が見つからない**: Python Launcher が入っている場合は `py -3 ...` で実行できます。
- **PowerShell で venv 有効化がブロックされる**: 管理者で PowerShell を開き、
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
  を一度実行してから `Activate.ps1` を再度実行してください。
- **途中中断で .tmp が残る**: `images\*.tmp` を削除して再実行してください。
  ```powershell
  Remove-Item -Force .\images\*.tmp -ErrorAction SilentlyContinue
  ```

## 注意事項
- サイトの利用規約・アクセス負荷に配慮してください。短時間の大量アクセスは避け、`--sleep` の設定を推奨します。
- 本スクリプトの利用により生じる問題は自己責任で対応してください。
