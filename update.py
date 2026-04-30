#!/usr/bin/env python3
"""
경쟁사 뉴스 자동 수집 스크립트
- 네이버 검색 API로 30개 경쟁사 최신 뉴스 수집
- template.html을 사용해 index.html 생성
- GitHub Actions가 cron + 수동 트리거로 실행
"""
import os
import sys
import json
import re
import requests
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET')

if not CLIENT_ID or not CLIENT_SECRET:
    print("ERROR: NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET 환경변수가 필요합니다.", file=sys.stderr)
    sys.exit(1)

KST = timezone(timedelta(hours=9))

COMPANIES = {
    "POS / 테이블오더 / 키오스크": [
        {"name": "티오더", "query": "티오더 테이블오더", "desc": "태블릿 기반 테이블오더 1위. 누적 35만대 설치.", "tags": ["테이블오더","태블릿","AI"], "type": "direct"},
        {"name": "페이히어", "query": "페이히어 POS", "desc": "모바일 POS 기반 소상공인 매장관리 솔루션.", "tags": ["모바일POS","SaaS"], "type": "direct"},
        {"name": "하나시스", "query": "하나시스 키오스크", "desc": "POS·키오스크 전문기업. HW+SW 통합.", "tags": ["POS","키오스크","프랜차이즈"], "type": "direct"},
        {"name": "포스뱅크", "query": "포스뱅크 POS", "desc": "POS·키오스크 하드웨어 제조. 글로벌 수출.", "tags": ["POS하드웨어","키오스크","수출"], "type": "indirect"},
        {"name": "오케이포스", "query": "오케이포스 POS", "desc": "POS·키오스크·VAN 사업 겸영.", "tags": ["POS","키오스크","VAN"], "type": "indirect"},
        {"name": "캐치테이블", "query": "캐치테이블 예약", "desc": "레스토랑 예약·웨이팅 플랫폼.", "tags": ["예약","웨이팅","외식"], "type": "indirect"},
        {"name": "메뉴잇", "query": "메뉴잇 모바일오더", "desc": "QR 기반 모바일 오더 서비스.", "tags": ["QR오더","비대면"], "type": "indirect"},
        {"name": "한국전자금융", "query": "한국전자금융 키오스크", "desc": "코스닥 상장 키오스크 전문. 무인결제·식권·주차.", "tags": ["키오스크","무인결제","코스닥"], "type": "kiosk"},
        {"name": "씨아이테크", "query": "씨아이테크 키오스크", "desc": "키오스크·DID 전문 상장기업.", "tags": ["키오스크","DID","공공"], "type": "kiosk"},
        {"name": "니스인프라", "query": "NICE인프라 키오스크", "desc": "NICE그룹 키오스크 제조. 대형 고객사 다수.", "tags": ["키오스크","NICE그룹"], "type": "kiosk"},
        {"name": "성신이노텍", "query": "성신이노텍 키오스크", "desc": "키오스크 전문 제조. 무인주문·결제·발권.", "tags": ["키오스크제조","무인주문"], "type": "kiosk"},
        {"name": "푸른기술", "query": "푸른기술 키오스크", "desc": "식권·세금환급 키오스크. 한국전자금융 협업.", "tags": ["식권키오스크","세금환급"], "type": "kiosk"},
    ],
    "결제 (PG / VAN)": [
        {"name": "토스플레이스", "query": "토스플레이스", "desc": "토스 오프라인 결제 단말기. 가맹점 30만+.", "tags": ["결제단말기","토스"], "type": "direct"},
        {"name": "한국신용데이터(KCD)", "query": "한국신용데이터 캐시노트", "desc": "캐시노트 운영. 200만 사업장.", "tags": ["캐시노트","소상공인금융"], "type": "direct"},
        {"name": "KG이니시스", "query": "KG이니시스", "desc": "국내 1위 PG사.", "tags": ["PG","온오프라인"], "type": "eco"},
        {"name": "NHN한국사이버결제(KCP)", "query": "NHN한국사이버결제", "desc": "NHN 계열 PG사.", "tags": ["PG","NHN"], "type": "eco"},
        {"name": "헥토파이낸셜", "query": "헥토파이낸셜", "desc": "PG·VAN 통합. 간편결제·송금.", "tags": ["PG","VAN"], "type": "eco"},
        {"name": "KICC", "query": "한국정보통신 KICC", "desc": "VAN·PG 겸업. 오프라인 결제 핵심.", "tags": ["VAN","PG"], "type": "eco"},
        {"name": "KPN", "query": "한국결제네트웍스", "desc": "VAN사. 소상공인 결제 단말기.", "tags": ["VAN","단말기"], "type": "eco"},
        {"name": "나이스페이먼츠", "query": "나이스페이먼츠", "desc": "나이스그룹 PG사.", "tags": ["PG","나이스"], "type": "eco"},
        {"name": "토스페이먼츠", "query": "토스페이먼츠", "desc": "토스 온라인 PG. 개발자 친화적.", "tags": ["PG","API"], "type": "eco"},
    ],
    "멤버십 / 브랜드앱": [
        {"name": "발트루스트", "query": "발트루스트 Valtrust", "desc": "매장 멤버십·브랜드앱 솔루션. CRM.", "tags": ["멤버십","브랜드앱","CRM"], "type": "direct"},
        {"name": "도도포인트", "query": "도도포인트 스포카", "desc": "태블릿 포인트 적립. 고객관리.", "tags": ["포인트적립","고객관리"], "type": "indirect"},
        {"name": "채널톡", "query": "채널톡 채널코퍼레이션", "desc": "AI 고객 메신저. 통합 CRM.", "tags": ["메신저","CRM","AI"], "type": "indirect"},
        {"name": "리뷰노트", "query": "리뷰노트 크리마", "desc": "리뷰 관리·마케팅 자동화.", "tags": ["리뷰","마케팅"], "type": "indirect"},
    ],
    "빅테크 / 플랫폼": [
        {"name": "네이버", "query": "네이버페이 스마트주문", "desc": "네이버페이·스마트주문·예약.", "tags": ["네이버페이","스마트주문"], "type": "bigtech"},
        {"name": "카카오", "query": "카카오페이 톡주문", "desc": "카카오페이·톡주문·선물하기.", "tags": ["카카오페이","톡주문"], "type": "bigtech"},
        {"name": "토스", "query": "토스페이 비바리퍼블리카", "desc": "결제 생태계. 토스페이·플레이스.", "tags": ["토스페이","슈퍼앱"], "type": "bigtech"},
        {"name": "배달의민족", "query": "배달의민족 우아한형제들", "desc": "배달앱 1위. 배민오더 확장.", "tags": ["배달","매장주문"], "type": "bigtech"},
        {"name": "당근", "query": "당근 동네가게 당근페이", "desc": "로컬 플랫폼. 동네가게·당근페이.", "tags": ["로컬커머스","당근페이"], "type": "bigtech"},
    ],
}

TYPE_KEYWORDS = {
    "실적": ["흑자", "매출", "영업이익", "분기 실적", "당기순이익", "성장세"],
    "투자": ["투자 유치", "투자유치", "시리즈", "유치한", "기업가치", "유니콘", "라운드"],
    "제휴": ["제휴", "협업", "MOU", "파트너십", "공동 개발"],
    "신규서비스": ["출시", "런칭", "오픈", "공개", "선보", "신제품", "신규"],
    "인사": ["임명", "선임", "사임", "신임 대표", "신임 CEO"],
    "규제": ["규제", "법안", "정책", "당국", "과태료", "처분"],
}

def classify_news(title, summary):
    text = (title + " " + summary).lower()
    for type_name, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                return type_name
    return "뉴스"

def clean_html_text(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = (text.replace('&quot;', '"')
                .replace('&amp;', '&')
                .replace('&lt;', '<')
                .replace('&gt;', '>')
                .replace('&apos;', "'")
                .replace('&#39;', "'")
                .replace('&nbsp;', ' '))
    return text.strip()

def fetch_news(query, display=5):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }
    params = {"query": query, "display": display, "sort": "date"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        return r.json().get("items", [])
    except Exception as e:
        print(f"  ERROR fetching '{query}': {e}", file=sys.stderr)
        return []

def parse_pubdate(pubdate_str):
    try:
        dt = parsedate_to_datetime(pubdate_str)
        return dt.astimezone(KST).strftime("%Y-%m-%d")
    except Exception:
        return ""

def get_source_from_url(url):
    if not url:
        return ""
    m = re.match(r'https?://(?:www\.|m\.)?([^/]+)', url)
    return m.group(1) if m else ""

def collect_all_news(days=14):
    cutoff = datetime.now(KST) - timedelta(days=days)
    news_data = {}
    for category, companies in COMPANIES.items():
        print(f"\n[{category}]")
        for c in companies:
            items = fetch_news(c['query'])
            filtered = []
            for item in items:
                pub_dt_str = item.get('pubDate', '')
                try:
                    pub_dt = parsedate_to_datetime(pub_dt_str)
                    if pub_dt < cutoff:
                        continue
                except Exception:
                    pass
                title = clean_html_text(item.get('title', ''))
                summary = clean_html_text(item.get('description', ''))
                url = item.get('originallink') or item.get('link', '')
                filtered.append({
                    "title": title,
                    "summary": summary[:200],
                    "source": get_source_from_url(url),
                    "url": url,
                    "date": parse_pubdate(pub_dt_str),
                })
            news_data[c['name']] = filtered
            print(f"  {c['name']}: {len(filtered)}건")
    return news_data

def generate_highlights(news_data, max_items=5):
    all_news = []
    for company, items in news_data.items():
        if items:
            top = items[0]
            all_news.append({
                "company": company,
                "title": top["title"],
                "summary": top["summary"][:150],
                "type": classify_news(top["title"], top["summary"]),
                "_date": top["date"],
            })
    all_news.sort(key=lambda x: x.get("_date", ""), reverse=True)
    return [{k: v for k, v in n.items() if not k.startswith("_")} for n in all_news[:max_items]]

def generate_companies_meta():
    out = {}
    for category, companies in COMPANIES.items():
        out[category] = [{
            "name": c["name"],
            "desc": c["desc"],
            "tags": c["tags"],
            "type": c["type"],
        } for c in companies]
    return out

def render_html(news_data, highlights, last_updated):
    with open('template.html', 'r', encoding='utf-8') as f:
        template = f.read()
    template = template.replace(
        '/*__NEWS_DATA__*/',
        'const NEWS_DATA = ' + json.dumps(news_data, ensure_ascii=False) + ';'
    )
    template = template.replace(
        '/*__HIGHLIGHTS__*/',
        'const HIGHLIGHTS = ' + json.dumps(highlights, ensure_ascii=False) + ';'
    )
    template = template.replace(
        '/*__LAST_UPDATED__*/',
        'const LAST_UPDATED = ' + json.dumps(last_updated, ensure_ascii=False) + ';'
    )
    template = template.replace(
        '/*__COMPANIES__*/',
        'const COMPANIES = ' + json.dumps(generate_companies_meta(), ensure_ascii=False) + ';'
    )
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(template)
    print(f"\n[OK] index.html 생성 완료 ({last_updated})")

if __name__ == "__main__":
    print("=" * 60)
    print("경쟁사 뉴스 수집 시작")
    print("=" * 60)
    news_data = collect_all_news(days=14)
    highlights = generate_highlights(news_data)
    last_updated = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    total_news = sum(len(v) for v in news_data.values())
    print(f"\n총 수집 뉴스: {total_news}건")
    print(f"하이라이트: {len(highlights)}건")
    render_html(news_data, highlights, last_updated)
