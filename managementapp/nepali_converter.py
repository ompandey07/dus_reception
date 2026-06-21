import datetime

NEPALI_MONTHS = [
    "Baisakh", "Jestha", "Ashar", "Shrawan", "Bhadra", "Ashoj",
    "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra"
]

# We use an anchor date where we know the exact mapping.
# 2026-04-14 is Baisakh 1, 2083 BS.
ANCHOR_AD = datetime.date(2026, 4, 14)
ANCHOR_BS_YEAR = 2083
ANCHOR_BS_MONTH = 1
ANCHOR_BS_DAY = 1

# Dictionary of year -> list of days in each month (1 to 12).
# You can easily edit these numbers if Hamro Patro changes!
BS_MONTH_DAYS = {
    2082: [31, 31, 32, 31, 31, 30, 30, 29, 30, 29, 30, 30],
    2083: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30], # User can change Mangsir to 31 if they want!
    2084: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 29, 30],
}

def get_bs_data_for_ad_date(ad_date_str):
    try:
        parts = ad_date_str.split('-')
        target_ad = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
        
        days_diff = (target_ad - ANCHOR_AD).days
        
        current_year = ANCHOR_BS_YEAR
        current_month = ANCHOR_BS_MONTH
        current_day = ANCHOR_BS_DAY
        
        if days_diff >= 0:
            current_day += days_diff
            while True:
                days_in_month = BS_MONTH_DAYS.get(current_year, [30]*12)[current_month - 1]
                if current_day <= days_in_month:
                    break
                current_day -= days_in_month
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1
        else:
            days_diff = abs(days_diff)
            current_day -= days_diff
            while current_day <= 0:
                current_month -= 1
                if current_month < 1:
                    current_month = 12
                    current_year -= 1
                days_in_month = BS_MONTH_DAYS.get(current_year, [30]*12)[current_month - 1]
                current_day += days_in_month
                
        return {
            'year': current_year,
            'month': current_month,
            'day': current_day,
            'str_month': NEPALI_MONTHS[current_month - 1]
        }
    except Exception as e:
        print(f"Converter error: {e}")
        return None
