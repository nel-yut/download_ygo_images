Yu-Gi-Oh! DB 画像一括ダウンローダ（Windows）
概要

Yu-Gi-Oh! DB のカード詳細ページ（cid）一覧から、カード画像をダウンロードして保存します。

入力: cid 一覧ファイル（例: cids.txt）

出力: images\<cid>.<ext>（例: images\12424.png）

既存ファイルのスキップ、リトライ、アクセス間隔（sleep）に対応

Content-Type: application/octet-stream でも、実体が画像であれば自動判定して保存します

動作環境

Windows 10 / 11

Python 3.10 以上推奨（3.12/3.13 でも可）

PowerShell または コマンドプロンプト

ファイル構成（例）
yugioh-image-downloader/
├─ download_yugioh_images.py
├─ cids.txt
└─ images/              # 実行後に作成される

1. Python の導入（Windows）
1.1 Python をインストール

以下のいずれかでインストールしてください。

Microsoft Store で「Python 3.x」をインストール
または

python.org の Windows Installer を利用

注意:

python.org のインストーラを利用する場合は、必ず “Add python.exe to PATH” にチェックを入れてください。

1.2 動作確認

PowerShell を開いて以下を実行します。

python --version


Python 3.x.x が表示されれば OK です。
もし python が見つからない場合は、代替として以下で確認できます。

py -3 --version

2. 作業フォルダへ移動

PowerShell で作業フォルダへ移動します。

cd C:\path\to\yugioh-image-downloader

3. 仮想環境（venv）の作成と依存関係インストール（推奨）

venv を使うと、Python 環境を汚さずに依存関係を管理できます。

3.1 venv 作成
python -m venv .venv

3.2 venv 有効化

PowerShell:

.\.venv\Scripts\Activate.ps1


コマンドプロンプト（cmd）:

.\.venv\Scripts\activate.bat


有効化されると、プロンプト先頭に (.venv) が表示されます。


PowerShell で venv の Activate がブロックされる場合（ExecutionPolicy 対応）

PowerShell で .\.venv\Scripts\Activate.ps1 を実行した際に、次のようなエラーが出る場合があります。

running scripts is disabled on this system

この場合は、自分のユーザ（CurrentUser）だけ スクリプト実行を許可します（管理者権限不要）。

PowerShell で以下を実行

Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned


その後、venv を有効化

.\.venv\Scripts\Activate.ps1


確認（任意）

python --version
pip --version


補足:

RemoteSigned は「ローカル作成のスクリプトは許可、インターネット由来は署名が必要」という設定です。

会社PCなどでポリシーが固定されている場合、上記が拒否されることがあります。その場合は管理者（情シス）へ確認してください。

3.3 依存インストール
python -m pip install --upgrade pip
pip install requests beautifulsoup4 lxml

4. cid 一覧ファイル（cids.txt）の準備

cids.txt を作成して cid を列挙してください。

1行1cid でも、空白区切りでも可

# で始まる行はコメントとして無視されます

例: cids.txt

# sample
12424
9074
10522
6114

5. 実行方法
5.1 基本実行（既存ファイルがあればスキップ）
python download_yugioh_images.py --cid-file cids.txt --skip-existing

5.2 負荷を抑える（推奨）

アクセス負荷軽減のため、待機時間とリトライを増やします。

python download_yugioh_images.py --cid-file cids.txt --skip-existing --sleep 0.8 --retries 4

6. 出力仕様

出力先: images\

ファイル名: <cid>.<ext>

例: images\12424.png

拡張子は実体に合わせて自動判定します（.png/.jpg/.webp/.gif 等）

7. 主要オプション

--cid-file <path>: cid 一覧ファイル（必須）

--outdir <dir>: 出力ディレクトリ（デフォルト: images）

--locale <en|ja|...>: request_locale（デフォルト: en）

--sleep <sec>: cid ごとの待機秒（デフォルト: 0.4）

--retries <n>: 失敗時リトライ回数（デフォルト: 2）

--timeout <sec>: HTTP タイムアウト（デフォルト: 30）

--skip-existing: images\<cid>.* が存在する場合はスキップ

8. トラブルシューティング
8.1 python が見つからない

Python Launcher が入っている場合、以下で実行できます。

py -3 download_yugioh_images.py --cid-file cids.txt --skip-existing

8.2 PowerShell で Activate がブロックされる

実行ポリシーで venv の activate がブロックされる場合、PowerShell を管理者で開いて一度だけ以下を実行します。

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser


その後、再度:

.\.venv\Scripts\Activate.ps1

8.3 途中中断後に .tmp が残る

images\*.tmp を削除して再実行してください。

Remove-Item -Force .\images\*.tmp -ErrorAction SilentlyContinue

9. 注意事項

サイトの利用規約・アクセス負荷に配慮してください。短時間の大量アクセスは避け、--sleep の設定を推奨します。

本スクリプトの利用により生じたいかなる問題についても、利用者の責任でご対応ください。