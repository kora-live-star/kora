import requests
from bs4 import BeautifulSoup
import json
import re
import base64
import os

# ==========================================
# قاعدة بيانات قنوات DaddyLive (رقم السيرفر)
# تحتوي على جميع قنوات beIN Sports وغيرها
# ==========================================
DADDYLIVE_CHANNELS = {
    "بى ان سبورت 1": "74",
    "بى ان سبورت 2": "75",
    "بى ان سبورت 3": "76",
    "بى ان سبورت 4": "77",
    "بى ان سبورت 5": "78",
    "بى ان سبورت 6": "79",
    "بى ان سبورت 7": "80",
    "بى ان سبورت 8": "81",
    "بى ان سبورت 9": "82",
    "بى ان سبورت الاخبارية": "83",
    "بى ان سبورت المفتوحة": "84",
    "بى ان سبورت afc": "85",
    "بى ان سبورت afc 1": "85",
    "بى ان سبورت afc 2": "86",
    "بى ان سبورت afc 3": "87",
    "بى ان سبورت اكسترا 1": "88",
    "بى ان سبورت اكسترا 2": "89",
    "بى ان سبورت xtra 1": "88",
    "بى ان سبورت xtra 2": "89",
    "بى ان سبورت الانجليزية 1": "90",
    "بى ان سبورت الانجليزية 2": "91",
    "بى ان سبورت الفرنسية 1": "92",
    "ssc sport 1": "111",
    "ssc sport 2": "112",
    "ssc sport 3": "113",
    "ssc extra 1": "114",
    "الكاس 1": "121",
    "الكاس 2": "122",
    "ابو ظبى الرياضية": "120",
    "ufc": "150",
    "espn": "43",
    "espn+": "44",
    "tnt sports 1": "55"
}

DADDYLIVE_DOMAIN = "https://dlhd.so/embed/stream-"

def get_live_matches():
    print("🚀 جاري سحب المباريات من الموقع المصدر...")
    URL = "https://www.yallakora.com/match-center"
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        all_matches = []
        all_streams = {} 
        match_cards = soup.select('.matchCard') 
        
        for card in match_cards:
            try:
                # استخراج أسماء الفرق والشعارات والتوقيت
                team1 = card.select_one('.teamA p').text.strip()
                team2 = card.select_one('.teamB p').text.strip()
                logo1 = card.select_one('.teamA img')['src']
                logo2 = card.select_one('.teamB img')['src']
                match_time = card.select_one('.time').text.strip()
                
                # توليد ID مميز للمباراة
                clean_id = re.sub(r'\W+', '_', f"{team1}_vs_{team2}").lower()

                # استخراج اسم القناة
                channel_div = card.select_one('.channel')
                channel_name = channel_div.text.strip() if channel_div else "غير محدد"

                # تحديد حالة المباراة
                status_text = card.select_one('.matchStatus span').text.strip() if card.select_one('.matchStatus') else ""
                status = "soon"
                if "جارية" in status_text or "مباشر" in status_text:
                    status = "live"
                elif "انتهت" in status_text:
                    status = "finished"

                # حفظ بيانات المباراة
                match_entry = {
                    "id": clean_id,
                    "team1": team1,
                    "team2": team2,
                    "logo1": logo1,
                    "logo2": logo2,
                    "time": match_time,
                    "status": status,
                    "league": "بطولة اليوم",
                    "commentator": channel_name 
                }
                all_matches.append(match_entry)
                
                # البحث عن القناة في القاموس لتوليد رابط البث
                stream_number = None
                for key, val in DADDYLIVE_CHANNELS.items():
                    if key in channel_name.lower():
                        stream_number = val
                        break
                
                # توليد وتشفير الرابط إذا وجدنا القناة
                if stream_number:
                    embed_url = f"{DADDYLIVE_DOMAIN}{stream_number}.php"
                    encoded_url = base64.b64encode(embed_url.encode('utf-8')).decode('utf-8')
                    all_streams[clean_id] = [{"name": f"سيرفر المشاهدة ({channel_name})", "type": "iframe", "url_base64": encoded_url}]
                else:
                    all_streams[clean_id] = []
                
            except Exception:
                # تخطي أي مباراة تفشل في التحليل
                continue

        # حفظ الملفات
        if all_matches:
            with open('matches.json', 'w', encoding='utf-8') as f:
                json.dump(all_matches, f, ensure_ascii=False, indent=4)
            with open('streams.json', 'w', encoding='utf-8') as f:
                json.dump(all_streams, f, ensure_ascii=False, indent=4)
            print(f"✅ تمت العملية بنجاح! تم استخراج {len(all_matches)} مباراة وتوليد الروابط.")
        else:
            print("⚠️ لم يتم العثور على مباريات.")

    except Exception as e:
        print(f"❌ خطأ فني أثناء الاتصال: {e}")

if __name__ == "__main__":
    get_live_matches()