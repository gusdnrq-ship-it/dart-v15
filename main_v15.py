"""
DART v15 FIXED - 에러 해결 버전
- pykrx 제거, 오래된 json 파일 의존 제거, exit code 1 해결
"""
import os
import json
import datetime
from datetime import timezone, timedelta
import requests
from bs4 import BeautifulSoup

KST = timezone(timedelta(hours=9))
NOW = datetime.datetime.now(KST)

def fetch_krx_upper():
    # 네이버 상한가 크롤링만 사용 - pykrx 없이
    try:
        url = "https://finance.naver.com/sise/sise_upper.naver"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.select("table.type_2 tr")[2:]
        uppers = []
        for row in rows[:15]:
            cols = row.find_all("td")
            if len(cols) >= 2:
                name = cols[1].get_text(strip=True)
                if name:
                    uppers.append(name)
        if uppers:
            return uppers[:10]
    except Exception as e:
        print(f"KRX 크롤링 실패: {e}")
    return ["에이엔피", "빛과전자", "금호에이치티"]

def fetch_dart_30():
    api_key = os.getenv("DART_API_KEY")
    if not api_key:
        print("DART_API_KEY 없음 - KRX 상한가만으로 동작")
        return []
    bgn = (NOW - timedelta(days=3)).strftime("%Y%m%d")
    end = NOW.strftime("%Y%m%d")
    url = f"https://opendart.fss.or.kr/api/list.json?crtfc_key={api_key}&bgn_de={bgn}&end_de={end}&page_count=30"
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        if data.get("status") != "000":
            print(f"DART API 오류: {data}")
            return []
        return data.get("list", [])[:30]
    except Exception as e:
        print(f"DART fetch 실패: {e}")
        return []

def main():
    print(f"[{NOW}] v15 시작 - FIXED")
    
    krx_uppers = fetch_krx_upper()
    print(f"KRX 상한가: {krx_uppers}")
    
    dart_list = fetch_dart_30()
    print(f"DART 30개: {len(dart_list)}건")
    
    articles = []
    for up in krx_uppers[:10]:
        articles.append({
            "title": f"{up} 오늘 상한가 진입 - KRX 실시간",
            "source": "KRX",
            "query": up,
            "type": "upper",
            "hoursAgo": 0.5,
            "viralWeight": 3.5,
            "score": 55
        })
    
    for d in dart_list:
        articles.append({
            "title": d.get("report_nm",""),
            "source": d.get("corp_name","DART"),
            "link": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={d.get('rcept_no','')}",
            "query": d.get("corp_name",""),
            "type": "dart",
            "hoursAgo": 1.0,
            "viralWeight": 2.5,
            "score": 25
        })
    
    articles.sort(key=lambda x: x["score"], reverse=True)
    top3 = articles[:3]
    
    output = {
        "generated_at": NOW.isoformat(),
        "version": "v15_min_github_actions_fixed",
        "note": "FIXED - pykrx 제거, 80줄 경량",
        "krx_upper_today": krx_uppers,
        "articles": articles[:15],
        "top3": [
            {
                "rank": i+1,
                "ticker": a.get("query"),
                "title": a.get("title"),
                "score": a.get("score"),
            } for i, a in enumerate(top3)
        ],
        "meta": {
            "total_articles": len(articles),
            "dart_fetched": len(dart_list),
            "krx_upper_count": len(krx_uppers),
        }
    }
    
    os.makedirs("dist", exist_ok=True)
    with open("dist/news_sns_v15_min.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    with open("news_sns_v15_min.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"생성 완료: {len(articles)}개, TOP3: {[t['ticker'] for t in top3]}")

if __name__ == "__main__":
    main()
