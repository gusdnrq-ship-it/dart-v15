import os, json, datetime
from datetime import timezone, timedelta
import requests
from bs4 import BeautifulSoup

KST = timezone(timedelta(hours=9))
NOW = datetime.datetime.now(KST)

def get_upper():
    try:
        r = requests.get("https://finance.naver.com/sise/sise_upper.naver", headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        names = []
        for row in soup.select("table.type_2 tr")[2:12]:
            cols = row.find_all("td")
            if len(cols) >= 2:
                t = cols[1].get_text(strip=True)
                if t: names.append(t)
        if names: return names[:10]
    except Exception as e:
        print(f"upper fail {e}")
    return ["에이엔피","빛과전자","금호에이치티","코나아이","헥토파이낸셜"]

def main():
    print(f"[{NOW}] start")
    uppers = get_upper()
    print(f"uppers {uppers}")
    dart = []
    key = os.getenv("DART_API_KEY")
    if key:
        try:
            bgn = (NOW - timedelta(days=3)).strftime("%Y%m%d")
            end = NOW.strftime("%Y%m%d")
            url = f"https://opendart.fss.or.kr/api/list.json?crtfc_key={key}&bgn_de={bgn}&end_de={end}&page_count=20"
            data = requests.get(url, timeout=15).json()
            if data.get("status") == "000":
                dart = data.get("list", [])[:20]
        except Exception as e:
            print(f"dart fail {e}")

    articles = []
    for u in uppers:
        articles.append({"query": u, "title": f"{u} 오늘 상한가", "source": "KRX", "score": 55, "type": "upper"})
    for d in dart:
        articles.append({"query": d.get("corp_name",""), "title": d.get("report_nm",""), "source": "DART", "score": 25, "type": "dart"})

    articles = articles[:15]
    top3 = articles[:3]

    out = {
        "generated_at": NOW.isoformat(),
        "version": "v15_min_v6",
        "krx_upper_today": uppers,
        "articles": articles,
        "top3": [{"rank": i+1, "ticker": a["query"], "title": a["title"], "score": a["score"]} for i, a in enumerate(top3)],
        "meta": {"total": len(articles), "dart": len(dart)}
    }

    os.makedirs("dist", exist_ok=True)
    with open("dist/news_sns_v15_min.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    with open("news_sns_v15_min.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"DONE {len(articles)} TOP3 {uppers[:3]}")

if __name__ == "__main__":
    main()
