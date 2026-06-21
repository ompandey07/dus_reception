import requests
from bs4 import BeautifulSoup
from django.core.cache import cache
from datetime import datetime

# Nepali numerals mapping
NEPALI_NUMBERS = {
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4', 
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
}

NEPALI_MONTHS = [
    "Baisakh", "Jestha", "Ashar", "Shrawan", "Bhadra", "Ashoj",
    "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra"
]

def to_english_num(nepali_str):
    res = ""
    for char in nepali_str:
        res += NEPALI_NUMBERS.get(char, char)
    return int(res) if res.isdigit() else res

def get_bs_data_for_ad_date(ad_date_str):
    """
    Given an AD date string (YYYY-MM-DD or YYYY-M-D), 
    returns a dictionary with exact BS date from Hamro Patro scraper.
    Cached for fast subsequent retrievals.
    """
    # Let's see if we can get a fast guess for BS year/month using adbs to know which page to scrape
    # Wait, we need the adbs to know which page to scrape.
    from adbs import ad_to_bs
    try:
        bs_guess = ad_to_bs(ad_date_str.replace("-", "/"))
        bs_year = bs_guess['en']['year']
        bs_month = bs_guess['en']['month']
        
        # Scrape that specific BS month
        cache_key = f"hamro_month_{bs_year}_{bs_month}"
        month_data = cache.get(cache_key)
        
        if not month_data:
            month_data = scrape_hamro_month(bs_year, bs_month)
            if month_data:
                cache.set(cache_key, month_data, 60*60*24*7) # Cache for 7 days
                
        # Format input ad date to strip zero-padding if any, since HamroPatro uses YYYY-M-D
        parts = [int(x) for x in ad_date_str.split('-')]
        hp_id = f"{parts[0]}-{parts[1]}-{parts[2]}"
        
        if month_data and hp_id in month_data:
            return month_data[hp_id]
            
        # If not found (maybe the guess was off by 1 month at the edge)
        # Try previous month
        prev_month = bs_month - 1
        prev_year = bs_year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1
            
        prev_cache_key = f"hamro_month_{prev_year}_{prev_month}"
        prev_month_data = cache.get(prev_cache_key)
        if not prev_month_data:
            prev_month_data = scrape_hamro_month(prev_year, prev_month)
            if prev_month_data:
                cache.set(prev_cache_key, prev_month_data, 60*60*24*7)
                
        if prev_month_data and hp_id in prev_month_data:
            return prev_month_data[hp_id]
            
        # Try next month
        next_month = bs_month + 1
        next_year = bs_year
        if next_month == 13:
            next_month = 1
            next_year += 1
            
        next_cache_key = f"hamro_month_{next_year}_{next_month}"
        next_month_data = cache.get(next_cache_key)
        if not next_month_data:
            next_month_data = scrape_hamro_month(next_year, next_month)
            if next_month_data:
                cache.set(next_cache_key, next_month_data, 60*60*24*7)
                
        if next_month_data and hp_id in next_month_data:
            return next_month_data[hp_id]

        # Final fallback
        return bs_guess['en']
    except Exception as e:
        print(f"Scraper error: {e}")
        return None

def scrape_hamro_month(bs_year, bs_month):
    url = f"https://www.hamropatro.com/calendar/{bs_year}/{bs_month}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        days_li = soup.find_all('li', id=True)
        month_map = {}
        for li in days_li:
            if '-' in li['id']:
                try:
                    nep_span = li.find('span', class_='nep')
                    if nep_span:
                        nep_day_str = nep_span.text.strip()
                        day_num = to_english_num(nep_day_str)
                        
                        month_map[li['id']] = {
                            'year': bs_year,
                            'month': bs_month,
                            'day': day_num,
                            'str_month': NEPALI_MONTHS[bs_month - 1]
                        }
                except Exception:
                    pass
        return month_map
    except Exception as e:
        print(f"Failed to scrape {bs_year}/{bs_month}: {e}")
        return None
