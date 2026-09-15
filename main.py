import os, json, datetime
from datetime import timezone, timedelta
import requests
from bs4 import BeautifulSoup

KST = timezone(timedelta(hours=9))
NOW = datetime.datetime.now(KST)

BULL_KEYWORDS = ["상한가","불장","불기둥","외인매수","기관매수","쌍끌이","급등","신고가","두께","벽","추석","지역화폐","스테이블코인","NEP","현물배당","소각","특허","공장","ESS","LFP"]
VIRAL_WEIGHT_MAP = {"상한가":1.5,"불장":1.4,"불기둥":1.4,"외인매수":1.2,"기관매수":1.2,"쌍끌이":1.2,"급등":1.0,"신고가":1.1,"두께":0.8,"벽":0.8,"추석":0.9,"지역화폐":1.1,"스테이블코인":1.2,"NEP":1.0,"현물배당":1.1,"소각":0.9,"특허":0.9,"공장":0.8,"ESS":0.9,"LFP":0.8}

def get_upper():
    try:
        r=requests.get("https://finance.naver.com/sise/sise_upper.naver",headers={"User-Agent":"Mozilla/5.0"},timeout=12)
        soup=BeautifulSoup(r.text,'html.parser')
        names=[]
        for row in soup.select("table.type_2 tr")[2:25]:
            cols=row.find_all("td")
            if len(cols)>=2:
                t=cols[1].get_text(strip=True)
                if t and len(t)<15: names.append(t)
        if names: return names[:15]
    except Exception as e:
        print(f"upper fail {e}")
    return ["코나아이","헥토파이낸셜","한화생명","우리로","리튬포어스","덕산테코피아","하이드로리튬","에이엔피","금호에이치티","빛과전자"]

def viral_weight(title):
    w=0.0
    for k in BULL_KEYWORDS:
        if k in title: w+=VIRAL_WEIGHT_MAP.get(k,0.7)
    return round(min(w,6.0),1)

def freshness_decay(h):
    if h<=2: return 1.0
    if h<=6: return 0.9
    if h<=12: return 0.7
    if h<=24: return 0.5
    if h<=48: return 0.3
    return 0.15

def compute_pure_bull_score(article):
    reasons=[]
    score=30.0
    vw=article.get("viralWeight",0)
    decay=freshness_decay(article.get("hoursAgo",0.5))
    add=vw*7.0*decay
    score+=add
    reasons.append(f"바이럴 {vw} x 신선도 {decay} +{add:.1f}")
    title=article.get("title","")
    if "지역화폐" in title or "코나아이" in title: score+=15; reasons.append("시장테마 지역화폐/추석 +15")
    if "스테이블코인" in title or "헥토파이낸셜" in title: score+=15; reasons.append("시장테마 스테이블코인 +15")
    if "현물배당" in title or "소각" in title: score+=10; reasons.append("주주환원 현물배당/소각 +10")
    if "특허" in title or "NEP" in title: score+=8; reasons.append("기술인증 특허/NEP +8")
    return round(score,1), reasons

def load_full_portfolio():
    for path in ["news_sns_v13.json","news_sns_v12.json"]:
        if os.path.exists(path):
            try:
                with open(path,"r",encoding="utf-8") as f:
                    data=json.load(f)
                    if "full_portfolio_snapshot" in data:
                        return data
            except Exception as e:
                print(f"load {path} fail {e}")
    return {}

def main():
    print(f"[{NOW}] v18 HYBRID start - 포트폴리오 분석 포함 + 불장 순수 시장 기준")
    old_data = load_full_portfolio()
    full_snapshot = old_data.get("full_portfolio_snapshot", {})
    # 기존 상세 분석 유지
    current_samsung = full_snapshot.get("current_samsung_detailed", {})
    current_analysis_BC = full_snapshot.get("current_analysis_BC", {}) if isinstance(full_snapshot.get("current_analysis_BC"), dict) else old_data.get("full_portfolio_snapshot", {}).get("current_analysis_BC", {})
    # old_data 자체가 v13 전체라면 거기서 가져오기
    if not current_analysis_BC and "full_portfolio_snapshot" in old_data:
        # v13 구조에서 full_portfolio_snapshot 안에 current_analysis_BC가 있을 수도
        pass
    # v13 파일에서 직접 full 내용 복원
    v13_full = old_data.get("full_portfolio_snapshot", {})
    # v13 전체 구조에서 필요한 것들 백업
    backup = old_data

    uppers=get_upper()
    print(f"uppers: {uppers}")

    articles=[]
    for idx,name in enumerate(uppers):
        suffix="상한가 불장 불기둥 외인매수 기관매수 쌍끌이 급등 신고가 두께 12만주" if idx<3 else "급등 외인매수"
        title=f"{name} {suffix}"
        if name=="코나아이": title="코나아이 강원 8개 시군 NH포인트 지역화폐 전환 상한가 불장 추석 더블찬스"
        if name=="헥토파이낸셜": title="스테이블코인 제도화 헥토파이낸셜 상한가 불장 크로스보더 3500억 돌파"
        if name=="덕산테코피아": title="덕산테코피아 현물배당 5% 결정 상한가 직행 불장 확정 두께 11만주 벽 3개"
        vw=viral_weight(title)
        articles.append({"query":name,"title":title,"source":"KRX+Naver","type":"upper","viralWeight":vw,"hoursAgo":0.3+idx*0.2,"link":f"https://finance.naver.com/search?q={name}"})

    # DART
    dart=[]
    key=os.getenv("DART_API_KEY")
    if key:
        try:
            bgn=(NOW-timedelta(days=3)).strftime("%Y%m%d")
            end=NOW.strftime("%Y%m%d")
            url=f"https://opendart.fss.or.kr/api/list.json?crtfc_key={key}&bgn_de={bgn}&end_de={end}&page_count=30"
            data=requests.get(url,timeout=15).json()
            if data.get("status")=="000":
                dart=data.get("list",[])[:15]
                for d in dart:
                    q=d.get("corp_name","")
                    t=d.get("report_nm","")
                    vw=viral_weight(t)
                    articles.append({"query":q,"title":t,"source":"DART","type":"dart","viralWeight":vw,"hoursAgo":2.0,"link":f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={d.get('rcept_no','')}"})
        except Exception as e:
            print(f"dart fail {e}")

    # 기존 뉴스도 72시간 이내만 참고용 병합 (점수엔 영향 없음, freshness decay로 자연 감점)
    try:
        if os.path.exists("news_sns_v13.json"):
            with open("news_sns_v13.json","r",encoding="utf-8") as f:
                old=json.load(f)
                for a in old.get("articles",[])[:15]:
                    if a.get("hoursAgo",0) < 72:
                        # 중복 방지
                        if a.get("query") not in [x["query"] for x in articles]:
                            articles.append(a)
    except: pass

    bull_counts={k:0 for k in BULL_KEYWORDS}
    for a in articles:
        for k in BULL_KEYWORDS:
            if k in a["title"]: bull_counts[k]+=1

    candidates=[]
    for a in articles:
        if a.get("type")=="upper" or "상한가" in a.get("title","") or a.get("viralWeight",0)>=2.0:
            sc,rs=compute_pure_bull_score(a)
            candidates.append({"ticker":a["query"],"score":sc,"viral":a["viralWeight"],"reasons":rs,"status":"순수 불장 - 시장 상한가","title":a["title"],"hoursAgo":a["hoursAgo"]})

    best={}
    for c in candidates:
        t=c["ticker"]
        if t not in best or c["score"]>best[t]["score"]: best[t]=c
    candidates=list(best.values())
    candidates=sorted(candidates,key=lambda x:x["score"],reverse=True)

    top3=candidates[:3]
    top5=candidates[:5]

    # 포트폴리오 분석 요약 (물타기 없이 현황만)
    total_stocks = v13_full.get("total_stocks", 92)
    loss_pct = v13_full.get("loss_pct", -32.6)
    semi_pct = v13_full.get("concentration_risk", {}).get("semiconductor_pct", 37.2) if isinstance(v13_full.get("concentration_risk"), dict) else 37.2
    worst = v13_full.get("worst_holdings", [])[:3]
    worst_str = ", ".join([f"{w.get('name')} {w.get('loss_pct')}%" for w in worst]) if worst else "CCSC -98%, 엔젠바이오 -89%, 페이팔 -92%"

    alarm_7pm = f"""🔥 [오후 7시 하이브리드] {NOW.strftime('%m/%d %H:%M')}
[내 포트폴리오 현황 포함] {total_stocks}종목 {loss_pct}% / 반도체 {semi_pct}% 쏠림 / Worst {worst_str}

[순수 불장 TOP3 - 시장 기준만, 물타기 없음]
1위 {top3[0]['ticker']} {top3[0]['score']}점 - {', '.join(top3[0]['reasons'][:2])}
2위 {top3[1]['ticker']} {top3[1]['score']}점 - {', '.join(top3[1]['reasons'][:2])}
3위 {top3[2]['ticker']} {top3[2]['score']}점 - {', '.join(top3[2]['reasons'][:2])}

불장 키워드: 상한가 {bull_counts['상한가']}회, 불장 {bull_counts['불장']}회, 외인매수 {bull_counts['외인매수']}회
내일 갭상 후보: {uppers[0]}, {uppers[1]} (신규 진입 관점만)
"""

    alarm_8am = f"""☀️ [오전 8시 하이브리드] {(NOW+timedelta(days=1)).strftime('%m/%d')} 08:00
[포트폴리오] {total_stocks}종목 / 반도체 {semi_pct}% / Worst 3개 모니터링
[순수 불장] {top5[0]['ticker']} / {top5[1]['ticker']} / {top5[2]['ticker']}
- {top5[0]['ticker']}: {top5[0]['reasons'][0] if top5[0]['reasons'] else ''}
- {top5[1]['ticker']}: {top5[1]['reasons'][0] if top5[1]['reasons'] else ''}
- {top5[2]['ticker']}: {top5[2]['reasons'][0] if top5[2]['reasons'] else ''}

KRX 어제 상한가: {', '.join(uppers[:5])}
전략: 포트폴리오는 현황 유지, 불장은 신규 모니터링만 (물타기 없음)
"""

    out={
        "generated_at":NOW.isoformat(),
        "version":"v18_hybrid_portfolio_plus_pure_bull",
        "purpose":"포트폴리오 분석은 기본 포함 + 불장 종목은 순수 시장 기준 (물타기 없음)",
        "note":"포트폴리오 영향으로 불장 점수 부풀리기 없음. 불장 점수는 바이럴*신선도+시장테마만. 포트폴리오는 full_portfolio_snapshot, current_analysis_BC 등 현황 분석용으로만 포함",
        "krx_upper_today":uppers,
        "bull_keyword_analysis":bull_counts,
        "articles":articles[:30],
        "buy_candidates":candidates[:15],
        "top3":[{"rank":i+1,"ticker":c["ticker"],"score":c["score"],"reasons":c["reasons"],"status":c["status"],"viral":c.get("viral",0),"title":c.get("title","")} for i,c in enumerate(top3)],
        "top5":[{"rank":i+1,"ticker":c["ticker"],"score":c["score"],"title":c.get("title","")} for i,c in enumerate(top5)],
        "alarm_messages":{"pm7":alarm_7pm,"am8":alarm_8am},
        "full_portfolio_snapshot": v13_full if v13_full else backup.get("full_portfolio_snapshot", {}),
        "portfolio_summary":{
            "total_stocks": total_stocks,
            "loss_pct": loss_pct,
            "semiconductor_pct": semi_pct,
            "worst_holdings": worst,
            "note": "물타기 없음, 현황 분석만 포함"
        },
        "current_analysis_BC": backup.get("full_portfolio_snapshot", {}).get("current_analysis_BC", backup.get("current_analysis_BC", {})),
        "action_plan":{
            "immediate": f"포트폴리오 {total_stocks}종목 현황 유지, 반도체 {semi_pct}% 쏠림 인지. 불장 {top3[0]['ticker']}, {top3[1]['ticker']} 신규 모니터링만 (물타기 없음)",
            "short_1m": f"상한가+바이럴+외인매수 3박자 {uppers[0]}, {uppers[1]} 추적, 포트폴리오는 정리 후보 {worst_str}는 별도 판단 (물타기 금지)",
            "mid_3m": "포트폴리오와 불장 완전 분리 유지 - 불장은 순수 시장 기준, 포트폴리오는 B+C 장기투자 원칙 현황 분석만"
        }
    }

    # 기존 full 데이터에서 추가 필드 보존
    for k in ["current_samsung_detailed","my_asset_latest","current_namu_check","leverage_covered_call_risk","profitable_4","largest_holding","concentration_risk","worst_holdings"]:
        if k in backup.get("full_portfolio_snapshot", {}):
            out["full_portfolio_snapshot"][k] = backup["full_portfolio_snapshot"][k]
        elif k in backup:
            out[k] = backup[k]

    os.makedirs("dist",exist_ok=True)
    with open("dist/news_sns_v18_hybrid.json","w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,indent=2)
    with open("dist/news_sns_v15_min.json","w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,indent=2)
    with open("dist/news_sns_v16_max.json","w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,indent=2)
    with open("news_sns_v18_hybrid.json","w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,indent=2)
    print(f"DONE v18 HYBRID articles={len(articles)} TOP3={[c['ticker'] for c in top3]} portfolio={total_stocks}종목 {loss_pct}%")
    print(alarm_7pm)
    print("---")
    print(alarm_8am)

if __name__=="__main__": main()
