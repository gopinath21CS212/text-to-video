import os
import re
import requests
from bs4 import BeautifulSoup
import mysql.connector
from gtts import gTTS
from langdetect import detect
from translate import Translator as TranslateTranslator

# Function to sanitize a string for use as a filename
def sanitize_filename(filename):
    return re.sub(r'[\\/:*?"<>|]', '_', filename)

# Function to clean text
def clean_text(text):
    # Replace non-breaking spaces with regular spaces
    cleaned_text = text.replace('\xa0', ' ')

    # Remove non-printable characters and control characters
    cleaned_text = ''.join(filter(lambda x: x.isprintable(), cleaned_text))

    return cleaned_text

def translate_text(text):
    try:
        # Detect the source language
        detected_language = detect(text)
        if detected_language:
            print(f"Detected language: {detected_language}")

            # Translate the text using the translate library
            translator = TranslateTranslator(to_lang='en', from_lang=detected_language)
            translated_text = translator.translate(text)

            if translated_text:
                return translated_text
            else:
                print("Translation failed.")
                return None
        else:
            print("Language detection failed or unsupported language.")
            return None
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return None

def generate_captions(translated_text, url):
    try:
        # Create the directory for saving captions
        captions_dir = 'captions'
        if not os.path.exists(captions_dir):
            os.makedirs(captions_dir)

        # Generate captions from translated text
        captions_file_path = os.path.join(captions_dir, f"{sanitize_filename(url)}_en.srt")

        # Write the captions to an SRT file
        with open(captions_file_path, 'w', encoding='utf-8') as captions_file:
            lines = translated_text.split('\n')
            for i, line in enumerate(lines, start=1):
                caption = f"{i}\n{line}\n\n"
                captions_file.write(caption)

        return captions_file_path
    except Exception as e:
        print(f"Caption generation error: {str(e)}")
        return None

def scrape_translate_generate_voiceover(url):
    try:
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
            body = soup.find('body')
            if body:
                scraped_text = body.get_text()
                cleaned_text = clean_text(scraped_text)  # Clean the scraped text
            else:
                scraped_text = ''
                cleaned_text = ''

            db_connection = mysql.connector.connect(
                host="localhost",
                user="gopi",
                password="gopivip9940@",
                database="sih",
                charset="utf8mb4",  # Set the character set to utf8mb4
            )

            with db_connection.cursor() as cursor:
                insert_query = "INSERT INTO scraped_data (url, content) VALUES (%s, %s)"
                data = (url, cleaned_text)
                cursor.execute(insert_query, data)
                db_connection.commit()

                # Translate the cleaned text
                translated_text = translate_text(cleaned_text)

                if translated_text:
                    # Create the directory for saving voiceovers if it doesn't exist
                    voiceovers_dir = 'voiceovers'
                    if not os.path.exists(voiceovers_dir):
                        os.makedirs(voiceovers_dir)

                    # Generate a voiceover for the translated text in English
                    tts = gTTS(text=translated_text, lang='en')

                    # Sanitize the URL for use as a filename
                    sanitized_url = sanitize_filename(url)

                    # Save the voiceover to an audio file with a sanitized filename
                    voiceover_audio_path = os.path.join(voiceovers_dir, f"{sanitized_url}_en.mp3")
                    tts.save(voiceover_audio_path)

                    # Generate captions from translated text
                    captions_file_path = generate_captions(translated_text, url)

                    if captions_file_path:
                        # Update the database with the voiceover audio file path, translated text, and captions
                        update_query = "UPDATE scraped_data SET translated_text = %s, voiceover_audio = %s, captions = %s WHERE url = %s"
                        data = (translated_text, voiceover_audio_path, captions_file_path, url)
                        cursor.execute(update_query, data)
                        db_connection.commit()

                        print("Scraped data, translated text, voiceover, and captions generated and saved.")
                else:
                    print("Translation failed.")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if db_connection.is_connected():
            db_connection.close()

if __name__ == "__main__":
    url_to_scrape = 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=1953999'
    scrape_translate_generate_voiceover(url_to_scrape)
