了解です。それでは会社PCでの実演用に、そのまま手順をコピペして使える **README.md** を作ります。以下の内容で十分にカバーできます。

---

````markdown
# LINEチャットボット 実演用手順

## 1. リポジトリのクローン

```bash
# GitHub リポジトリをクローン
git clone https://github.com/<username>/<repo>.git
cd <repo>
````

既にある場合は最新に更新：

```bash
git pull
```

---

## 2. Python 仮想環境の作成

```bash
# Python 3.12 以上を前提
python3 -m venv venv
source venv/bin/activate
```

---

## 3. 依存ライブラリのインストール

```bash
pip install --upgrade pip
pip install flask line-bot-sdk
```

* `flask`：管理画面・Webhook 用
* `line-bot-sdk`：LINE Messaging API 用

---

## 4. 環境変数の設定

Linux 端末で以下を設定：

```bash
export LINE_CHANNEL_ACCESS_TOKEN="あなたのアクセストークン"
export LINE_CHANNEL_SECRET="あなたのシークレット"
export OPERATOR_ID="管理者のLINE ID"
export PORT=8000
```

> 安全のため、`.env` にまとめて Git には含めないようにするのが推奨です。

---

## 5. Flask サーバーの起動

```bash
source venv/bin/activate  # 仮想環境アクティブ化
python main.py
```

* デフォルトで `0.0.0.0:8000` に待機
* ブラウザでアクセス：`http://<PCのIP>:8000/admin`

---

## 6. 管理画面の確認

* `/admin` → チャット管理画面
* `/editor` → シナリオ編集画面
* チャットの発言は左がユーザー、右がボット
* アイコン・名前も正しく表示されます
* 現在適用中のシナリオが画面上に表示されます

---

## 7. LINE Webhook 設定（実機デモ用）

* 社内ネットワークから LINE へ Webhook を公開する必要があります
* 一時的な公開なら `ngrok` が便利：

```bash
ngrok http 8000
```

* 生成された URL を LINE Developers の Webhook URL に設定：

```
https://xxxx.ngrok.io/callback
```

> これで LINE からのメッセージ受信・自動返信が可能になります

---

## 8. ブラウザ通知

* Edge / Chrome で通知を許可する必要があります
* 「通知」タイプのメッセージが届くと音付き通知が表示されます

---

## 9. デモ用操作

1. `/admin` でチャット画面を開く
2. ユーザーを選択してメッセージを送信
3. ボットが自動でシナリオに沿って返信
4. `/editor` でシナリオの編集・追加が可能
5. 編集後は管理画面で「適用中シナリオ」を切り替えて確認

---

### 補足

* `users.json`：ユーザー情報（名前・アイコン）
* `messages.json`：メッセージログ
* `scenarios.json`：シナリオ定義
* 仮想環境外の Python で実行すると依存関係不足で動かない可能性があります

```

---

これをそのまま会社PCにコピーすれば、Git クローン → 仮想環境 → 起動 → 管理画面でのデモ、という流れで簡単に実演できます。  

---

💡質問:  
この README に **ngrok を使わず、完全に社内 LAN だけでデモする方法** も追加した方がいいですか？
```
