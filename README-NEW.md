# DART v15 GitHub Actions - 처음부터 재설계

## 문제점 (현재 v12/v13 2026-09-09 고정)
- 1224줄 거대 JSON (92종목 스냅샷 포함) → 시트 `1VhCK57m...` 타임아웃
- 고정 쿼리 8개 (리튬포어스, 코나아이, 헥토) → 동일종목 95/88/88 반복
- GAS 6분 제한 → 100개 DART fetch 중 사망 → 시트 안 열림
- 로컬이면 PC off 시 알림 불가

## 새 구조 (GitHub Actions - PC off여도 동작)
```
GitHub Actions (Cloud, 매일 08:30 KST)
  ├─ 1. KRX 오늘 상한가 크롤링 (에이엔피, 빛과전자 등 매일 신규)
  ├─ 2. DART 30개만 (100→30) 필터: 현물배당/소각/특허/공장/NEP/ESS/실적
  ├─ 3. v15 스코어링: DART25 + 기술35(두께10만+벽3개+value1.5~2.5) + 뉴스20(리튬7.99%↑) + 전문가20(외인+기관)
  ├─ 4. freshness decay: 24h 100%, 24-48h 70%, 48-72h 30%, 72h+ 제외
  ├─ 5. 동일종목 방지: 한 종목 기사 3개 이상 시 스킵
  ├─ 6. 출력: news_sns_v15_min.json (80줄, TOP3만) → Drive 19NVe8jH... 업로드 + GitHub Pages 호스팅
  └─ 7. 알림: Meta AI 스케줄러가 min.json 읽어서 08:35/18:00 발송 (PC off여도 옴)

Google Sheets
  └─ IMPORTRANGE로 min.json만 읽음 (거대 JSON 안 읽음) → 절대 안 죽음

Local (PC 켜질 때만)
  └─ 호가창 조작 HC12, 두께, value 정밀 분석 → 결과만 Drive 덮어쓰기
```

## Secrets (절대 코드에 넣지 말 것)
- DART_API_KEY
- DRIVE_FOLDER_ID = 19NVe8jHuw789G1aXc8cgCLnvZrQ5g_Nn
- GOOGLE_SERVICE_ACCOUNT_JSON (Drive 업로드용)
- TELEGRAM_BOT_TOKEN (선택, 알림용)
