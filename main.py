from flask import Flask, render_template, request, send_file, send_from_directory, redirect, url_for
from transformers import pipeline
#from gtts import gTTS
from werkzeug.utils import secure_filename
import os
from fpdf import FPDF
import PyPDF2
from helper_functions import *

UPLOAD_FOLDER = 'static/files'
ALLOWED_EXTENSIONS = {'txt', 'rtf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def home():
    return render_template('/home.html')

@app.route("/summary", methods=["POST", "GET"])
def summarizer():
    if request.method == "POST":
        print("Analyzing text")
        #Get user input
        data = request.form['mytext']
        #Create summary
        summarizer = pipeline("summarization")
        result = summarizer(data, max_length=50)[0]['summary_text'] # fixed the limit error  
        print("Got a result")
        #Create pdf
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size = 15)
        pdf.multi_cell(200, 10, txt = result, align = "L")
        pdf.output(os.path.join(app.config['UPLOAD_FOLDER'], "sum.pdf"))
        print("PDF finished")

        directory = os.path.join(app.config['UPLOAD_FOLDER'])
        return send_from_directory(directory = directory, filename="sum.pdf", as_attachment=True) #fixed the positional argue errror
    else:
        print("We are here")
        return render_template('/home.html') 

@app.route("/upload",methods=["GET","POST"])
def files():
    if request.method=="POST":
        # Upload function
        file = request.files["file"]
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"],"user_input"+filename[-4:])) 
        print("Saved file")
        return redirect(url_for("files"))
    else:
        files = os.listdir(os.path.join(app.config["UPLOAD_FOLDER"]))
        return render_template("/home.html")

@app.route("/upload_to_audio", methods=["POST", "GET"])
def sumfile():
    if request.method == "POST":
        print("Initiating to convert upload to audio")
        #Finding uploaded content
        file_path = os.path.join("static", "files")
        file_content = os.listdir(file_path)
        user_input = ""
        for el in file_content:
            if el[:10] == "user_input":
                user_input = el
                print(user_input)
        
        file_path = os.path.join("static", "files", user_input)
        #Reading upload
        if user_input[-3:] == "pdf":
            print(user_input, "it´s a pdf")
            read_pdf = PyPDF2.PdfFileReader(open(file_path, "rb"))
            page_text = ""
            #Get starting and ending page
            try:
                spage = int(request.form['fname']) -1
                print(spage)
                epage = int(request.form['lname']) -1
            except:
                spage, epage = 0, read_pdf.getNumPages() -1

            for page in range(spage, epage):
                page_content = read_pdf.getPage(page)
                page_text += page_content.extractText()
            file = page_text
            print(spage,epage,page_text)
            # os.remove("static/files/book.txt")
            # with open("static/files/book.txt", "w",encoding="utf-8") as f:
            #     f.write(file)                



        elif user_input[-3:] == "txt" or "rtf":
            print(user_input, "it´s a txt")
            file = open(file_path, 'r')
            file = file.read()
        #Creating audio
        print("Creating audio")
        # print(file)
        speech = create_audiobook() #gTTS(text = str(file), lang = "en", tld='com.au', slow = False)
        speech.save(os.path.join(app.config['UPLOAD_FOLDER'], "voice.mp3"))


        print("Got a result")
        return send_file(os.path.join(app.config['UPLOAD_FOLDER'], "voice.mp3"),
                    #mimetype='audio/mp3',
                    #download_name='audiobook.mp3',
                    as_attachment=True)
    else:
        print("We are here")
        return render_template('/home.html') 

@app.route("/upload_sum_to_audio", methods=["POST", "GET"])
def sum_to_audio():
    if request.method == "POST":
        print("Summarize upload and create audio")
        # Finding upload from user
        file_path = os.path.join("static", "files")
        file_content = os.listdir(file_path)
        user_input = ""
        for el in file_content:
            if el[:10] == "user_input":
                user_input = el
                print("found",user_input)
        
        file_path = os.path.join("static", "files", user_input)
        #Creating audio for pdf
        if user_input[-3:] == "pdf":
            print(user_input, "it´s a pdf")
            pdf_file = open(file_path, 'rb')
            read_pdf = PyPDF2.PdfFileReader(pdf_file)
            try:
                spage = int(request.form['fname'])
                print(spage)
                epage = int(request.form['lname'])
            except:
                spage, epage = 1, read_pdf.getNumPages() 

            sentences = textify(read_pdf,spage,epage) # handling big books
            cleaned = cleaning(sentences)
            hf_summarizer(cleaned)
            create_audiobook()

            return send_file("static/audiobook/output.mp3",
                        #mimetype='audio/mp3',
                        #download_name='audiobook_summary.mp3',
                        as_attachment=True)
        #Creating audio for text
        elif user_input[-3:] == "rtf":
            print(user_input, "it´s a txt")
            with open(file_path, 'r') as f:
                file = f.read()
                result = summarizer(file)[0]['summary_text'] 


            print("Creating audio")
            speech = create_audiobook() #gTTS(text = str(result), lang = "en", slow = False)
            speech.save(os.path.join(app.config['UPLOAD_FOLDER'], "voice.mp3"))
            # os.system("start " + os.path.join(app.config['UPLOAD_FOLDER'], "voice.mp3"))

            # os.remove(os.path.join(app.config['UPLOAD_FOLDER'], "voice.mp3")) #Deleting file

            print("Got a result")
            return send_file(os.path.join(app.config['UPLOAD_FOLDER'], "voice.mp3"),
                        #mimetype='audio/mp3',
                        #download_name='audiobook_summary.mp3',
                        as_attachment=True)
    else:
        print("We are here")
        return render_template('/home.html') 

if __name__ == "__main__":
    app.run()

