# AI SIGNAL｜AI 產業觀測站

手機優先的繁體中文 AI 情報 Dashboard。深色介面、內嵌 SVG 圖示、主題/組織/日期/關鍵字篩選、來源查核、Markdown 匯出。

## 公開閱讀與私密收藏

- 公開情報不需登入。右上角「登入收藏」或「已存訊號」頁面可登入。
- 使用 Supabase Auth 的電子郵件與密碼登入。新帳戶需先驗證信箱。
- 個人收藏儲存在 `public.ai_signal_bookmarks`；RLS 限制每人只能讀寫自己的資料。
- 使用現有 Supabase `Tokyo-family-travel-expenses` 專案，資料表獨立；登入帳戶屬於同一個 Supabase 專案。未修改旅遊記帳資料表與既有權限。
- 前端只有 publishable key，不包含 service_role、管理金鑰或任何人的密碼。
- 原本的本機收藏不會自動上傳；登入後可在收藏頁明確選擇「匯入本機收藏」。
- 登出會清除畫面中的雲端收藏；不刪除雲端資料。同步失敗時會顯示重試，暫停修改。

## 建置與部署

使用 Node 24，依 package-lock.json 固定版本：

```sh
npm ci --ignore-scripts
npm run check
npm run build
```

`src/template.html`：版型與主要互動；`cloud.js`：登入與收藏同步；`data.json`：已查核消息；`config.json`：公開的 Supabase 專案 URL 與 publishable key。`npm run build` 會將 SDK 與應用程式打包到自含的 `dist/index.html`，並同步根目錄 `index.html`。不依賴 CDN。

GitHub Pages：Settings → Pages → Source 選 GitHub Actions，推送 main 或手動執行 Deploy AI Signal to GitHub Pages。也可直接以 main / root 發布已建置的 index.html。

## Supabase 登入網址

正式上線後，必須在 Authentication → URL Configuration 的 Redirect URLs 加入正式網站精確網址（含尾端斜線）。保留既有 Site URL，避免影響旅遊網站。註冊驗證及密碼重設都會以此網址為回跳目標。這一步尚需正式網址完成後確認。

目前專案 email provider 已啟用、允許註冊且必須驗證信箱。寄信額度與自訂 SMTP 依 Supabase 專案設定；不保證內建寄信可供大量外部使用。

## 已完成驗證

- JavaScript 語法與正式打包成功。
- 匿名 Data API 存取收藏回傳 401 / 42501。
- 已以兩個既有身分，在 rollback-only 交易中驗證：只能看到自己的測試收藏；可新增/刪除自己的資料；無法新增/刪除別人的資料。測試交易已回滾，無殘留測試資料。
- Supabase 安全顧問沒有回報新收藏表的警告；既有專案另有 SECURITY DEFINER 函式可執行權限及未啟用外洩密碼防護的警告，未擅自調整共享專案設定。
- 真正的帳戶登入、郵件回跳與跨裝置同步，仍須在正式網站與使用者帳戶完成端到端驗證。

## 情報資料與自動更新

目前消息來自 2026/11/01 對話試跑保留的三筆歷史官方公告，不是當日新訊或完整歷史資料庫；精確試跑時間未保留。

每日 08:00 新聞搜尋與摘要尚未啟用。現有 Pages workflow 只部署網站，不會自行產生新消息。未來搜尋/模型 API 金鑰只能設在 GitHub Actions secrets 或後端，不可放入此 repository 的前端設定。現有 ChatGPT 排程尚未與本網站連接。
