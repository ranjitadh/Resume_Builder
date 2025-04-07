import utils.session
from flask import Flask, render_template, request, send_file, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from fpdf import FPDF
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resumes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------- DATABASE MODEL ----------
class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    linkedin = db.Column(db.String(255))
    summary = db.Column(db.Text)
    skills = db.Column(db.Text)
    experience = db.Column(db.Text)
    education = db.Column(db.Text)

# ---------- PDF CLASS ----------
def safe_text(text):
    return (
        text.replace('–', '-').replace('—', '-')
            .replace('•', '-').replace('“', '"')
            .replace('”', '"').replace("’", "'")
    )

class ATSResume(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        self.set_font("Arial", size=12)

    def header_info(self, name, email, phone, linkedin):
        self.set_font("Arial", 'B', 16)
        self.cell(0, 10, safe_text(name.upper()), ln=True)
        self.set_font("Arial", '', 12)
        self.cell(0, 10, safe_text(f"{email} | {phone} | {linkedin}"), ln=True)
        self.ln(10)

    def add_section(self, title, content_list):
        self.set_font("Arial", 'B', 14)
        self.cell(0, 10, safe_text(title), ln=True)
        self.set_font("Arial", '', 12)
        for item in content_list:
            self.multi_cell(0, 8, safe_text(f"- {item}"))
        self.ln(5)

    def save_to_memory(self):
        pdf_bytes = self.output(dest='S').encode('latin1')
        buffer = io.BytesIO(pdf_bytes)
        buffer.seek(0)
        return buffer

# ---------- ROUTES ----------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        form = request.form

        # Save to DB
        new_resume = Resume(
            name=form["name"],
            email=form["email"],
            phone=form["phone"],
            linkedin=form["linkedin"],
            summary=form["summary"],
            skills=form["skills"],
            experience=form["experience"],
            education=form["education"]
        )
        db.session.add(new_resume)
        db.session.commit()

        # Generate PDF
        resume = ATSResume()
        resume.header_info(form["name"], form["email"], form["phone"], form["linkedin"])
        resume.add_section("PROFESSIONAL SUMMARY", form["summary"].split("\n"))
        resume.add_section("TECHNICAL SKILLS", form["skills"].split("\n"))
        resume.add_section("EXPERIENCE", form["experience"].split("\n"))
        resume.add_section("EDUCATION", form["education"].split("\n"))

        pdf = resume.save_to_memory()
        return send_file(pdf, download_name="resume.pdf", as_attachment=True)

    return render_template("index.html")

@app.route("/submissions")
def submissions():
    all_resumes = Resume.query.all()
    return render_template("submissions.html", resumes=all_resumes)

# ---------- MAIN ----------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
