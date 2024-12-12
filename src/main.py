import json
import random
import openai
from datetime import datetime
import calendar as _calendar
import argparse

# File paths
QUOTES_FILE = "src/data/quotes.json"
CALENDAR_FILE = "src/data/calendar.json"

# Model and System Message
OPENAI_MODEL = "gpt-4o"
SYSTEM_MSG = """
I will provide a Stoic quote. Write a calm, thoughtful explanation of its underlying meaning, suitable for someone new to Stoic philosophy.
Present your response as a single cohesive paragraph, integrating contemporary scenarios to illustrate the idea in everyday life.
Begin directly with your interpretation—without using phrases like “this quote means...” or “the quote is saying...”
—and let the wording of the quote guide your explanation naturally.
Maintain an accessible, relatable tone that connects the ancient wisdom to modern circumstances.
"""

def get_stoic_quote_of_the_day():
    today = datetime.now()
    year = str(today.year)
    day_of_year = today.timetuple().tm_yday
    days_in_year = 366 if _calendar.isleap(int(year)) else 365

    with open(QUOTES_FILE, "r", encoding="utf-8") as f:
        quotes = json.load(f)

    with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
        calendar = json.load(f)

    if year not in calendar:
        uuids = list(quotes.keys())
        calendar = {year: random.sample(uuids, days_in_year)}
        with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
            json.dump(calendar, f, indent=4, ensure_ascii=False)

    uuid = calendar[year][day_of_year - 1]
    return quotes[uuid]

def get_stoic_interpretation_api(quote_text, author):
    """
    Fetches interpretation from OpenAI API.
    """
    try:
        client = openai.Client()
        user_msg = f"{quote_text} - {author}"

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_MSG},
                {"role": "user", "content": user_msg},
            ],
            temperature=1,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            max_tokens=500,
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"API call failed: {e}")
        return None

def get_precomputed_interpretation(quote):
    """
    Selects a random precomputed interpretation from the quote's interpretations.
    """
    interpretations = quote.get("interpretations", [])
    if not interpretations:
        return None
    return random.choice(interpretations)

def parse_arguments():
    """
    Parses command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Generate Stoic Quote of the Day with Interpretation.")
    parser.add_argument(
        '--skip-api',
        action='store_true',
        help='Skip fetching interpretation from OpenAI API and use a precomputed interpretation instead.'
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    skip_api = args.skip_api

    quote = get_stoic_quote_of_the_day()
    text = quote["text"]
    author = quote["author"]
    today_date_str = datetime.now().strftime("%A, %B %d, %Y")

    interpretation = None

    if skip_api:
        # Use a precomputed interpretation
        interpretation = get_precomputed_interpretation(quote)
        if not interpretation:
            print("No precomputed interpretations available for this quote.")
    else:
        # Attempt to fetch interpretation from API
        interpretation = get_stoic_interpretation_api(text, author)
        if not interpretation:
            # Fallback to precomputed interpretation if API call fails
            interpretation = get_precomputed_interpretation(quote)
            if not interpretation:
                print("No precomputed interpretations available for this quote.")

    # Prepare HTML template
    # If interpretation is available, include it; otherwise just show the quote.
    html_template = f"""<h1 align="center">Stoic Quote of the Day</h1>
<p align="center"><em>{today_date_str}</em></p>
<p align="center">
    <em>"{text}"</em><br>
    <strong>— {author}</strong>
</p>
"""

    if interpretation:
        html_template += f"""
<p align="center" style="max-width:600px;margin:0 auto;">
    {interpretation}
</p>
"""

    # Update README
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(html_template)