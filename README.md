# AI SIGNAL｜AI 產業觀測站

正式網站：https://alston-chen02.github.io/ai-industry-dashboard/

## 移轉狀態

使用者指定使用其他 Supabase Organization 建立獨立 AI SIGNAL 專案。目前僅能存取 Personal Travel 組織，等待新組織名稱與連線，以及該組織的建置費用確認。

已將 `config.json` 設為 enabled:false；不建立 Supabase client、不發送登入或收藏請求。網站保留公開閱讀、分類/組織/日期/文字搜尋、來源查核、Markdown 匯出及手機導覽。右上角與收藏頁明確顯示登入服務建置中。

旅遊專案的 ai_signal_bookmarks 表在確認為空後已移除，原旅遊資料表不受影響。Dashboard 回跳網址也需自旅遊專案移除；不更動其 Site URL 或其他回跳網址。

## 待接續

1. 確認另一個 Organization 的名稱與存取權限。
2. 依該組織實際費用報價，完成新專案建立確認。
3. 建立獨立 AI SIGNAL 專案、套用 database/schema.sql、啟用 email auth、設定正式回跳網址。
4. 將該專案 URL、publishable key 與 enabled:true 寫入 config.json；執行 npm run build。
5. 部署後驗證登入、登出、雲端收藏與帳戶隔離。

## 程式與部署

Node 24。npm ci --ignore-scripts → npm run check → npm run build。

src/template.html 是版型與頁面程式，cloud.js 是登入與私密收藏整合，data.json 為已查核消息。建置將固定版本 SDK 與程式內嵌到 dist/index.html，並同步根目錄 index.html。不使用 CDN，不包含 service_role 或管理金鑰。

GitHub Pages 由 .github/workflows/pages.yml 部署。前端公開；個人收藏未來由獨立 Supabase Auth 與 RLS 保護。登入後可明確選擇匯入先前本機收藏；不會自動將本機清單上傳至任何帳戶。

## 驗證與資料範圍

已驗證手機版 390px 排版、篩選、來源檢視與登入視窗。移轉前收藏 RLS 已以兩個既有身分在 rollback-only 交易中驗證隔離、本人新增/刪除及禁止跨帳戶修改；無測試資料殘留。舊專案未成功登入任何新帳戶，不能宣稱完整端到端登入流程已通過。新專案建置後需重新驗證。

目前情報是 2026/11/01 試跑保留的三筆歷史官方公告；不是今日新訊或完整歷史資料。每日 08:00 搜尋、模型摘要與網站更新尚未啟用；現有 ChatGPT 排程也未與此網站連接。GitHub Actions 目前只部署網站。
