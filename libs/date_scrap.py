from dateparser.search import search_dates
from datetime import datetime, timedelta
import dateparser
import re

# Mapping of weekdays
WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6
}

# Clean unwanted connector words from parsed phrases
def clean_text(text):
    filter_words = {"and", "was", "were", "they", "those", "is"}
    return " ".join(word for word in text.split() if word.lower() not in filter_words)

# Get next or double-next weekday date
def get_next_weekday(weekday_name: str, double_next=False):
    today = datetime.today()
    weekday_name = weekday_name.lower()
    if weekday_name not in WEEKDAYS:
        return None

    today_weekday = today.weekday()
    target_weekday = WEEKDAYS[weekday_name]

    days_ahead = (target_weekday - today_weekday + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    if double_next:
        days_ahead += 7

    return today + timedelta(days=days_ahead)

# Main extraction function
def extract_dates(text):
    text = text.lower()
    output = []
    seen_dates = set()
    used_indices = []

    # 1a. Handle 'next <weekday> [optional time]'
    pattern_next_weekday = re.compile(
        r'\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
        r'(?:\s*(?:at|by|till)?\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?))?'
    )
    for match in pattern_next_weekday.finditer(text):
        day, time_str = match.groups()
        phrase = match.group(0)
        start, end = match.span()

        dt_date = get_next_weekday(day, double_next=True)

        if time_str:
            parsed_time = dateparser.parse(time_str.strip(), settings={
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': dt_date
            })
            if parsed_time:
                dt_date = dt_date.replace(hour=parsed_time.hour, minute=parsed_time.minute)

        date_str = dt_date.strftime('%d-%m-%Y')
        time_out = dt_date.strftime('%H:%M') if dt_date.time() != datetime.min.time() else None

        output.append({
            "phrase": phrase.strip(),
            "date": date_str,
            "day": dt_date.strftime('%A'),
            "time": time_out
        })

        seen_dates.add((date_str, time_out))
        used_indices.append((start, end))

    # 1b. Handle plain '<weekday> [optional time]'
    pattern_weekday = re.compile(
        r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
        r'(?:\s*(?:at|by|till)?\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?))?'
    )
    for match in pattern_weekday.finditer(text):
        day, time_str = match.groups()
        phrase = match.group(0)
        start, end = match.span()

        # Skip if overlaps with any previously handled 'next <weekday>'
        if any(start < used_end and end > used_start for used_start, used_end in used_indices):
            continue

        dt_date = get_next_weekday(day, double_next=False)

        if time_str:
            parsed_time = dateparser.parse(time_str.strip(), settings={
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': dt_date
            })
            if parsed_time:
                dt_date = dt_date.replace(hour=parsed_time.hour, minute=parsed_time.minute)

        date_str = dt_date.strftime('%d-%m-%Y')
        time_out = dt_date.strftime('%H:%M') if dt_date.time() != datetime.min.time() else None

        if (date_str, time_out) not in seen_dates:
            output.append({
                "phrase": phrase.strip(),
                "date": date_str,
                "day": dt_date.strftime('%A'),
                "time": time_out
            })
            seen_dates.add((date_str, time_out))
            used_indices.append((start, end))

    # 2. Use search_dates but skip overlaps
    results = search_dates(
        text,
        settings={
            'PREFER_DATES_FROM': 'future',
            'RELATIVE_BASE': datetime.now()
        }
    )

    if results:
        for phrase, dt in results:
            phrase_lower = phrase.lower().strip()
            start_idx = text.find(phrase_lower)
            end_idx = start_idx + len(phrase_lower)

            # Skip if overlaps with previously handled phrase
            if any(start < end_idx and end > start_idx for start, end in used_indices):
                continue

            date_str = dt.strftime('%d-%m-%Y')
            time_str = dt.strftime('%H:%M') if dt.time() != datetime.min.time() else None

            if (date_str, time_str) not in seen_dates and dt.date() >= datetime.today().date():
                output.append({
                    "phrase": phrase.strip(),
                    "date": date_str,
                    "day": dt.strftime('%A'),
                    "time": time_str
                })
                seen_dates.add((date_str, time_str))

    return output

# Extract topic by removing date/time expressions
def extract_topic(text):
    text = text.lower()

    # Remove date/time phrases
    date_phrases = search_dates(
        text,
        settings={
            'PREFER_DATES_FROM': 'future',
            'RELATIVE_BASE': datetime.now()
        }
    )

    cleaned_text = text
    if date_phrases:
        for phrase, _ in date_phrases:
            cleaned_text = cleaned_text.replace(phrase.lower(), '')

    # Remove temporal connector words
    cleaned_text = re.sub(r'\b(by|till|until|on|this|next|coming|before|after|at)\b', '', cleaned_text)

    # Remove weekday names
    cleaned_text = re.sub(r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', '', cleaned_text)

    # Normalize spacing and punctuation
    cleaned_text = re.sub(r'[.,!?]', '', cleaned_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

    return cleaned_text

# Test run
if __name__ == "__main__":
    query = "complete cleaning room till next sunday till 8pm"
    topic = extract_topic(query)
    print(f"Topic : {topic}")
    print("Extracted Dates:")
    for item in extract_dates(query):
        print(item)

    query2 = "complete cleaning room till sunday till 8pm"
    topic2 = extract_topic(query2)
    print(f"\nTopic : {topic2}")
    print("Extracted Dates:")
    for item in extract_dates(query2):
        print(item)
