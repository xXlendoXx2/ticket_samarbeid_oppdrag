from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "123"  # endre denne
# Opprett database-tabellen om den ikke finnes
def init_db():
    with sqlite3.connect("database.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS brukere (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                navn TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                passord TEXT NOT NULL,
                rolle TEXT NOT NULL CHECK(rolle IN ('bruker', 'ansatt'))
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ny_henvendelser (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                navn TEXT NOT NULL,
                email TEXT NOT NULL,
                problem TEXT NOT NULL,
                beskrivelse TEXT,
                status TEXT DEFAULT 'Ikke påbegynt',
                bruker_id INTEGER,
                ansatt_svar TEXT,
                bruker_svar TEXT,
                FOREIGN KEY (bruker_id) REFERENCES brukere(id)
            );
        """)
        
            
    

@app.route("/", methods=["GET", "POST"])
def home():
    if "bruker_id" not in session:
        return redirect("/registrer")

    if request.method == "POST":
        navn = session.get("navn")
        email = session.get("email")
        problem = request.form["problem"]
        beskrivelse = request.form["beskrivelse"]
        bruker_id = session.get("bruker_id")

        with sqlite3.connect("database.db") as conn:
            conn.execute("""
                INSERT INTO ny_henvendelser (navn, email, problem, beskrivelse, bruker_id)
                VALUES (?, ?, ?, ?, ?)
            """, (navn, email, problem, beskrivelse, bruker_id))
        
        return redirect("/henvendelser")

    rolle = session.get("rolle")
    bruker_id = session.get("bruker_id")

    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row
        if rolle == "ansatt":
            henvendelser = conn.execute("SELECT * FROM ny_henvendelser").fetchall()
        else:
            henvendelser = conn.execute("SELECT * FROM ny_henvendelser WHERE bruker_id = ?", (bruker_id,)).fetchall()

    return render_template("index.htm",
                           navn=session.get("navn"),
                           email=session.get("email"),
                           rolle=rolle,
                           ny_henvendelser=henvendelser)




@app.route("/henvendelser")
def henvendelser():
    if "bruker_id" not in session:
        return redirect("/logginn")
    
    bruker_id = session.get("bruker_id")
    rolle = session.get("rolle")

    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row
        if rolle == "ansatt":
            rows = conn.execute("SELECT * FROM ny_henvendelser").fetchall()
        else:
            rows = conn.execute("SELECT * FROM ny_henvendelser WHERE bruker_id = ?", (bruker_id,)).fetchall()
    return render_template("henvendelser.htm", ny_henvendelser=rows, rolle=rolle)

# En rute kun for ansatte
@app.route("/oppdater/<int:sak_id>", methods=["POST"])
def oppdater_sak(sak_id):
    if session.get("rolle") != "ansatt":
        return "Ikke autorisert", 403

    status = request.form["status"]
    ansatt_svar = request.form["ansatt_svar"]

    with sqlite3.connect("database.db") as conn:
        conn.execute("UPDATE ny_henvendelser SET status = ?, ansatt_svar = ? WHERE id = ?", (status, ansatt_svar, sak_id))
    
    return redirect("/henvendelser")
# En rute kun for brukere
@app.route("/svarbruker/<int:sak_id>", methods=["POST"])
def svarbruker(sak_id):
    if session.get("rolle") != "bruker":
        return "Ikke autorisert", 403

    bruker_svar = request.form["bruker_svar"]

    with sqlite3.connect("database.db") as conn:
        conn.execute("UPDATE ny_henvendelser SET bruker_svar = ? WHERE id = ?", (bruker_svar, sak_id))
    
    return redirect("/henvendelser")
@app.route("/registrer", methods=["GET", "POST"])
def registrer():
    session.clear()
    if request.method == "POST":
        navn = request.form["navn"]
        email = request.form["email"]
        passord = request.form["passord"]

        # Hvis passord starter med /*, gi rollen "ansatt", ellers "bruker"
        rolle = "ansatt" if passord.startswith("/*") else "bruker"

        with sqlite3.connect("database.db") as conn:
            conn.row_factory = sqlite3.Row
            eksisterende_bruker = conn.execute("SELECT * FROM brukere WHERE email = ?", (email,)).fetchone()
            if eksisterende_bruker:
                return "E-post er allerede registrert", 400

            hashed_passord = generate_password_hash(passord)
            conn.execute("""
                INSERT INTO brukere (navn, email, passord, rolle)
                VALUES (?, ?, ?, ?)
                """, (navn, email, hashed_passord, rolle))

        return redirect("/logginn")

    return render_template("registrer.htm")


@app.route("/logginn", methods=["GET", "POST"])
def logginn():
    session.clear()
    if request.method == "POST":
        email = request.form["email"]
        passord = request.form["passord"]

        with sqlite3.connect("database.db") as conn:
            conn.row_factory = sqlite3.Row
            bruker = conn.execute("SELECT * FROM brukere WHERE email = ?", (email,)).fetchone()

        if bruker and check_password_hash(bruker["passord"], passord):
            session["bruker_id"] = bruker["id"]
            session["navn"] = bruker["navn"]
            session["email"] = bruker["email"]

            # Hvis passordet starter med /*, gjør brukeren til ansatt i økten
            if passord.startswith("/*"):
                session["rolle"] = "ansatt"
            else:
                session["rolle"] = bruker["rolle"]

            return redirect("/")
        
        return render_template("logginn.htm", feil="Feil e-post eller passord")

    return render_template("logginn.htm")



@app.route("/loggut")
def logout():
    session.clear()
    return redirect("/logginn")

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host='0.0.0.0', port="")
