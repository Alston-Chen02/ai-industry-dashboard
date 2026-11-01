# AI SIGNAL｜AI 產業觀測站

正式網站：https://alston-chen02.github.io/ai-industry-dashboard/

## 專案層級

AI Signal 使用獨立 Supabase 專案；資料庫、Auth 使用者與金鑰皆與其他應用分開。

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

## 每日情報更新

`.github/workflows/refresh.yml` 每日台灣時間 08:00 執行，也可在 Actions → Refresh daily AI briefing → Run workflow 手動執行。GitHub 排程可能延遲。更新流程直接重新部署 Pages，不依賴機器人 commit 觸發另一份 workflow。

在 Repository Settings → Secrets and variables → Actions → New repository secret 新增 `OPENAI_API_KEY`，值為可使用 Responses API 與網頁搜尋的 OpenAI API key。金鑰只提供給 Actions，不進前端、不寫入 repository。不需要另外接搜尋供應商；目前使用 Responses API 的 web_search。模型預設 `gpt-4.1-mini`，可用 Actions variable `OPENAI_MODEL` 覆寫為相容模型。API 呼叫依該 API 帳戶計費。

每次更新最多兩次模型呼叫，搜尋最多六個工具呼叫、最多八則消息。僅收錄可信網域、實際搜尋來源，並讀取原網頁 metadata 核對含時區的原始發布時間是否落在過去 24 小時；日期不明、舊消息、未來時間、衝突時間及重複來源不收錄。AI 摘要明確標示未經人工逐則審閱，不宣稱已涵蓋全部產業消息。

`data.json` 保存消息與每天的期別；同一來源沿用 ID，讓收藏保持有效。`refresh-status.json` 保存最後嘗試與成功時間。缺少金鑰或更新失敗時保留上次情報，畫面顯示等待設定或失敗。零則可靠消息會留下一筆「無重大新訊」期別；候選全部未通過檢核則視為失敗，避免誤報平靜日。每日同日期重跑會替換該期內容，既有歷史消息保留。

目前資料仍為 2026/11/01 試跑的三筆歷史官方公告。GitHub 已設定 OPENAI_API_KEY。2026/11/01 已連結訂閱並領取 API 額度，正式搜尋已回傳可檢核來源。官方索引無法直連時會顯示搜尋範圍受限，不會宣稱已全面查核；每篇候選的原始時間檢核仍為必要條件。端到端試跑與資料更新狀態請見 Actions 與 refresh-status.json。既有 ChatGPT 排程與本站 Actions 為獨立流程。

本機驗證：`python3 -m unittest discover -s tests`、`npm run check`、`npm run build`。Python 測試使用合成資料，驗證來源、時間窗、去重、收藏 ID、無新訊與失敗保留資料，不呼叫真實 API。
