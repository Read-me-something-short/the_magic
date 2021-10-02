from datetime import timedelta

from flask import Flask, render_template, request, send_file, send_from_directory, redirect, url_for, session
from werkzeug.utils import secure_filename
from fpdf import FPDF
import PyPDF2
from helper_functions import *

UPLOAD_FOLDER = 'static/files'
ALLOWED_EXTENSIONS = {'txt', 'rtf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "hello"
app.permanent_session_lifetime = timedelta(minutes=5)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/summary", methods=["POST", "GET"])
def summarizer():
    if request.method == "POST":
        # Get user input
        data = request.form['mytext']

        # Create summary
        summarizer = pipeline("summarization")
        result = summarizer(data, max_length=50)[0]['summary_text']

        # Create pdf
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=15)
        pdf.multi_cell(200, 10, txt=result, align="L")
        pdf.output(os.path.join(app.config['UPLOAD_FOLDER'], "sum.pdf"))

        directory = os.path.join(app.config['UPLOAD_FOLDER'])
        return send_from_directory(directory=directory, filename="sum.pdf", as_attachment=True)
    else:
        return render_template('/home.html') 


@app.route("/upload", methods=["GET", "POST"])
def files():
    if request.method == "POST":
        # Upload function
        file = request.files["file"]
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"],"user_input"+filename[-4:]))
        return redirect(url_for("files"))
    else:
        files = os.listdir(os.path.join(app.config["UPLOAD_FOLDER"]))
        return render_template("/home.html")


@app.route("/upload_to_audio", methods=["POST", "GET"])
def sumfile():
    if request.method == "POST":

        # Finding uploaded content
        file_path = os.path.join("static", "files")

        file_path, user_input = get_file_path(file_path)

        # Reading upload
        if user_input[-3:] == "pdf":
            read_pdf = PyPDF2.PdfFileReader(open(file_path, "rb"))
            page_text = ""

            # Get starting and ending page
            try:
                spage = int(request.form['fname']) - 1
                epage = int(request.form['lname']) - 1
            except:
                spage, epage = 0, read_pdf.getNumPages() - 1

            for page in range(spage, epage):
                page_content = read_pdf.getPage(page)
                page_text += page_content.extractText()
            file = page_text

        elif user_input[-3:] == "txt" or "rtf":
            print(user_input, "it´s a txt")
            file = open(file_path, 'r')
            file = file.read()

        # Creating audio
        speech = create_audiobook()
        speech.save(os.path.join(app.config['UPLOAD_FOLDER'], "voice.mp3"))

        return send_file(os.path.join(app.config['UPLOAD_FOLDER'], "voice.mp3"), as_attachment=True)
    else:
        return render_template('/home.html') 


@app.route("/upload_sum_to_audio", methods=["POST", "GET"])
def sum_to_audio():
    if request.method == "POST":

        # Finding upload from user
        file_path, user_input = get_file_path()

        # Creating audio for pdf
        if user_input[-3:] == "pdf":

            pdf_file = open(file_path, 'rb')
            read_pdf = PyPDF2.PdfFileReader(pdf_file)
            try:
                spage = int(request.form['fname'])
                epage = int(request.form['lname'])
            except:
                spage, epage = 1, read_pdf.getNumPages() 

            sentences = textify(read_pdf,spage,epage) # handling big books
            cleaned = cleaning(sentences)
            hf_summarizer(cleaned)
            create_audiobook()

            return send_file("static/audiobook/output.mp3", as_attachment=True)

        # Creating audio for text
        elif user_input[-3:] == "rtf":

            with open(file_path, 'r') as f:
                file = f.read()
                result = summarizer(file)[0]['summary_text'] 

            speech = create_audiobook()
            speech.save(os.path.join(app.config['UPLOAD_FOLDER'], "voice.mp3"))

            return send_file(os.path.join(app.config['UPLOAD_FOLDER'], "voice.mp3"), as_attachment=True)
    else:
        return render_template('/home.html')


# @app.route("/login", methods=["POST", "GET"])
# def login():
#     if request.method == "POST":
#         session.permanent = True
#         user = request.form["nm"]
#         session["user"] = user
#         return redirect(url_for("user"))
#     else:
#         if "user" in session:
#             return redirect(url_for("user"))
#
#         return render_template("login.html")
#
#
# @app.route("/user")
# def user():
#     if "user" in session:
#         user = session["user"]
#         return f"<h1>{user}</h1>"
#     else:
#         return redirect(url_for("login"))
#
#
# @app.route("/logout")
# def logout():
#     session.pop("user", None)
#     return redirect(url_for("login"))


if __name__ == "__main__":
    app.run()

