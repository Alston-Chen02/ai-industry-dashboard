# AI SIGNAL｜AI 產業觀測站

正式網站：https://alston-chen02.github.io/ai-industry-dashboard/

## 專案層級

- Organization：Alston Workspace（既有 Pro 組織，原名 Personal Travel，ID kzcpumenstpgryivwfzy）。
- Project：AI Signal（fghxwiuetmhhfibohnav），東京區 ap-northeast-1。
- 原旅遊專案 Tokyo-family-travel-expenses 保留，不共用 AI Signal 的資料庫、Auth 使用者或 API 金鑰。
- 新專案建立報價為 US$10/月的額外專案運算費，依原組織帳單計算；不另建立一份 Pro 訂閱。

## 登入與收藏

公開情報不需登入。右上角「登入收藏」，或「已存訊號」頁面可登入。AI Signal 為全新獨立 Auth，第一次使用需點「第一次使用？建立帳戶」、驗證信箱後登入；原旅遊帳戶、GitHub 帳戶與 Supabase 後台帳戶不會自動變成 AI Signal 使用者。

收藏位於 public.ai_signal_bookmarks，RLS 限制每個帳戶只能讀寫自己的資料。匿名角色無存取權；authenticated 只授予 SELECT、INSERT、DELETE。登出會清除畫面資料，不刪除雲端收藏。同步失敗會提示重試並暫停修改。舊版本機收藏不會自動上傳，登入後可明確選擇匯入目前帳戶。

前端僅含 publishable key，不含 service_role、管理金鑰、資料庫密碼或使用者密碼。session storage key 依專案分開。

## 設定與部署

Node 24。npm ci --ignore-scripts → npm run check → npm run build。

src/template.html：版型與主要互動；cloud.js：登入與雲端收藏；data.json：查核後消息；config.json：新專案 URL、publishable key 與 enabled:true。建置將固定版本 SDK 與程式內嵌至 dist/index.html，再同步根目錄 index.html。不依賴 CDN。

GitHub Pages Source 為 GitHub Actions，.github/workflows/pages.yml 負責建置部署。新專案 Site URL 與 Redirect URLs 設為正式網站的精確網址（含尾端斜線）。旅遊專案曾加入的 AI 收藏表與回跳網址已移除，原旅遊資料與設定保留。

## 驗證

- 固定依賴安裝、語法檢查與正式建置成功。
- 新專案 Auth settings 回傳 email enabled、註冊開啟、必須驗證信箱。
- 新專案匿名 Data API 讀取收藏回傳 401 / 42501。
- 已於新專案使用 rollback-only 交易建立兩個無密碼的測試身分，驗證只能讀取自己的收藏、本人新增/刪除成功、跨帳戶新增被拒、跨帳戶刪除為零；交易回滾後使用者與收藏數皆為零。
- 新專案安全顧問未回報警告。
- 已檢查手機版排版、公開閱讀與登入視窗。全新專案沒有實際使用者；首次註冊的郵件傳遞、確認與跨裝置實際登入仍需使用者完成，未宣稱這部分端到端驗證通過。

## 情報與後續更新

目前情報來自 2026/11/01 試跑保留的三筆歷史官方公告，非當日新訊或完整歷史資料。每日 08:00 搜尋與模型摘要尚未啟用，現有 ChatGPT 排程尚未串接此站。GitHub Actions 目前僅部署網站。未來 API 金鑰應儲存於 Actions secrets 或後端，不可放入前端。
