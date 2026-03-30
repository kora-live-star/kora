import requests
from bs4 import BeautifulSoup
import json
import re
import base64
import time

# المصادر القوية (إذا تعطل واحد يعمل الآخر)
SOURCES = [
    "https://www.bein-match.fit",
    "https://kooora4life.com",
    "https://live.yalla-shoot-arabia.com"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/"
}

def clean_name(name):
    return name.replace('شعار', '').replace('مباراة', '').replace('بث مباشر', '').strip()

def scrape():
    final_matches = []
    final_streams = {}
    
    for url in SOURCES:
        print(f"📡 محاولة السحب من: {url}")
        try:
            session = requests.Session()
            response = session.get(url, headers=HEADERS, timeout=20)
            response.encoding = 'utf-8'
            if response.status_code != 200: continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # البحث عن البطاقات
            match_cards = soup.find_all('a', href=re.compile(r'/match/|/video/|html$'))
            
            if not match_cards: continue

            for card in match_cards:
                try:
                    m_url = card['href']
                    if not m_url.startswith('http'): m_url = url.rstrip('/') + '/' + m_url.lstrip('/')
                    
                    # استخراج الأسماء
                    imgs = card.find_all('img')
                    if len(imgs) >= 2:
                        t1 = clean_name(imgs[0].get('alt', 'فريق 1'))
                        t2 = clean_name(imgs[1].get('alt', 'فريق 2'))
                        l1, l2 = imgs[0].get('src', ''), imgs[1].get('src', '')
                    else: continue

                    m_id = re.sub(r'\W+', '_', f"{t1}_vs_{t2}").lower()
                    
                    # الوقت والنتيجة
                    time_txt = card.find(string=re.compile(r'\d{1,2}:\d{2}'))
                    m_time = time_txt.strip() if time_txt else "00:00"
                    
                    status = "soon"
                    c_html = str(card).lower()
                    if any(x in c_html for x in ["مباشر", "live", "الان"]): status = "live"
                    elif any(x in c_html for x in ["انتهت", "finished"]): status = "finished"

                    # سحب الروابط (دخول صفحة المباراة)
                    streams = []
                    if status != "finished":
                        print(f"   🔗 فحص الروابط لـ: {t1}")
                        time.sleep(1)
                        m_page = session.get(m_url, headers=HEADERS, timeout=10)
                        m_soup = BeautifulSoup(m_page.text, 'html.parser')
                        for iframe in m_soup.find_all('iframe'):
                            src = iframe.get('src') or iframe.get('data-src')
                            if src and 'http' in src and 'ads' not in src.lower():
                                if src.startswith('//'): src = 'https:' + src
                                b64 = base64.b64encode(src.encode()).decode()
                                streams.append({"name": "Server HD", "url_base64": b64})

                    final_matches.append({
                        "id": m_id, "team1": t1, "team2": t2, "logo1": l1, "logo2": l2,
                        "time": m_time, "status": status, "league": "الدوريات الكبرى", "commentator": "Bein Sports"
                    })
                    final_streams[m_id] = streams
                    
                except Exception: continue
            
            if final_matches: break # لو نجح مصدر واحد نكتفي به
            
        except Exception as e: print(f"❌ خطأ: {e}")

    with open('matches.json', 'w', encoding='utf-8') as f:
        json.dump(final_matches, f, ensure_ascii=False, indent=4)
    with open('streams.json', 'w', encoding='utf-8') as f:
        json.dump(final_streams, f, ensure_ascii=False, indent=4)
    print(f"🎉 تم بنجاح! وجدنا {len(final_matches)} مباراة.")

if __name__ == "__main__":
    scrape()