import aflr
import subprocess
import os

from transformers import pipeline

import API_KEYS

MINI_PATH = "static/audiobook/raw_audio/"
RESULT_PATH = "static/audiobook/output.mp3"


def textify(read_pdf, spage, epage):
    """reads the pdf and extracts the text from it"""

    page_text = ""
    for page in range(spage, epage):
        page_content = read_pdf.getPage(page)
        page_text += page_content.extractText()

    full_text = page_text
    return full_text


def cleaning(full_text):
    
    """removes unwanted characters from the text and creates sentences"""
    try:
        if open(RESULT_PATH):
            os.remove(RESULT_PATH)

    except Exception as e:
        print(str(e))

    text = full_text

    book = ''.join(text)
    book = book.replace('.', '.<eos>')
    book = book.replace('?', '?<eos>')
    book = book.replace('!', '!<eos>')

    sentences = book.split('<eos>')

    return sentences


def hf_summarizer(sentences):
    """using Huggingface to summarize the sentences after
    splitting into chunks and re-joining them after it has been processed."""

    max_chunk = 512
    current_chunk = 0
    chunks = []

    for sentence in sentences:
        if len(chunks) == current_chunk +1:
            if len(chunks[current_chunk]) + len(sentence.split()) <= max_chunk:
                chunks[current_chunk].extend(sentence.split())
            else:
                current_chunk += 1
                chunks.append(sentence.split())
        else:
            chunks.append(sentence.split())

    for chunk_id in range(len(chunks)):
        chunks[chunk_id] = ' '.join(chunks[chunk_id])

    summarizer = pipeline("summarization")
    summarized = summarizer(chunks, min_length=50, max_length=100,  do_sample=False)

    text = ''.join([sum["summary_text"] for sum in summarized])

    with open("static/files/book.txt", "w", encoding="utf-8") as f:
        f.write(text)
    
    return summarized


def create_audiobook():
    """creates the audio of the summary"""

    f = open("static/files/book.txt", "r",  encoding="utf-8")
    summary = f.read()

    all_words = summary.split('.')
    aflr.api_key = API_KEYS.KEY
    VOICE = "Matthew"
    current, total_chars, chunk_num, TEXT = 0, 0, 0, []
    while current < len(all_words) - 1:
        while total_chars <= 4999:
            TEXT.append(all_words[current])
            total_chars += len(all_words[current]) + 1
            current += 1
            if current == len(all_words):
                break
        
        if current < len(all_words):
            TEXT.pop()
            current -= 1
            total_chars = 0

        TEXT = ".".join(TEXT)

        SPEED = 80
        script = aflr.Script().create(
                                    scriptText=TEXT,
                                    projectName="may_the_4th",
                                    moduleName="evil",
                                    scriptName=f"{chunk_num}_evil_{VOICE}",
        )

        scriptId = script["scriptId"]

        response = aflr.Speech().create(
                        scriptId=scriptId, voice=VOICE, speed=SPEED)

        # mastering current
        response = aflr.Mastering().create(
            scriptId=scriptId)

        url = aflr.Mastering().retrieve(scriptId=scriptId)

        # or download
        file = aflr.Mastering().download(
            scriptId=scriptId,  destination=MINI_PATH
        )

        TEXT = []
        chunk_num += 1

    play_audio()


def play_audio():
    """stitches the audio files created in create_audio(), to return one audio file"""
    directory = os.fsencode(MINI_PATH)

    adp = []

    for file in os.listdir(directory):
        filename = os.fsdecode(file)

        if filename.endswith(".mp3"): 
            adp.append(MINI_PATH+filename)
    adp.sort()
    x = "|".join(adp)
    subprocess.call(['ffmpeg', '-i', f'concat:{x}', '-acodec', 'copy', RESULT_PATH])
    
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".mp3"):
            os.remove(MINI_PATH+filename)


def get_file_path(file_path):

    file_content = os.listdir(file_path)
    user_input = ""
    for el in file_content:
        if el[:10] == "user_input":
            user_input = el

    file_path = os.path.join("static", "files", user_input)
    return file_path, user_input