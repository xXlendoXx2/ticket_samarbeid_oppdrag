from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "123"  # endre denne
# Opprett database-tabellen om den ikke finnes
#1 er aktiv, 0 er inaktiv
# Rolle kan være "bruker" eller "ansatt"

def init_db():
    with sqlite3.connect("database.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS brukere (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                navn TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                passord TEXT NOT NULL,
                aktiv INTEGER DEFAULT 1, 
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

    return render_template("index.htm", navn=session.get("navn"), email=session.get("email"), rolle=rolle, ny_henvendelser=henvendelser)

@app.route("/henvendelser")
def henvendelser():
    if "bruker_id" not in session:
        return redirect("/logginn")
    
    bruker_id = session.get("bruker_id")
    rolle = session.get("rolle")

    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("""
            DELETE FROM ny_henvendelser
            WHERE bruker_id NOT IN (SELECT id FROM brukere)
        """)
        conn.commit()

        if rolle == "ansatt":
            rows = conn.execute("SELECT * FROM ny_henvendelser WHERE lukket = 0").fetchall()
        else:
            rows = conn.execute("SELECT * FROM ny_henvendelser WHERE bruker_id = ?", (bruker_id,)).fetchall()

    return render_template("henvendelser.htm", ny_henvendelser=rows, rolle=rolle)

@app.route("/lukk_henvendelse/<int:sak_id>", methods=["POST"])
def lukk_henvendelse(sak_id):
    if session.get("rolle") != "ansatt":
        return "Ikke autorisert", 403
    if "bruker_id" not in session:
        return redirect("/logginn")

    with sqlite3.connect("database.db") as conn:
        conn.execute("""
            UPDATE ny_henvendelser SET status = 'Lukket', lukket = 1 WHERE id = ?
        """, (sak_id,))
        conn.commit()

    return redirect("/henvendelser")


# En rute kun for ansatte
@app.route("/oppdater/<int:sak_id>", methods=["POST"])
def oppdater_sak(sak_id):
    if session.get("rolle") != "ansatt":
        return "Ikke autorisert", 403
    if "bruker_id" not in session:
        return redirect("/logginn")

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
    if "bruker_id" not in session:
        return redirect("/logginn")

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
            if bruker["aktiv"] == 1:
                session["bruker_id"] = bruker["id"]
                session["navn"] = bruker["navn"]
                session["email"] = bruker["email"]
                session["rolle"] = bruker["rolle"]
                if session["rolle"] == "ansatt":
                    return redirect("/henvendelser")
                elif session["rolle"] == "bruker":
                    return redirect("/")
                return redirect("/") 
            else:
                return render_template("logginn.htm", feil="Kontoen din er deaktivert.")
        else:
            return render_template("logginn.htm", feil="Feil e-post eller passord.")

    return render_template("logginn.htm")


@app.route("/rediger_brukere", methods=["GET", "POST"])
def admin_brukere():
    if session.get("rolle") != "ansatt":
        return "Ikke autorisert", 403
    if "bruker_id" not in session:
        return redirect("/logginn")

    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row
        if request.method == "POST":
            bruker_id = request.form.get("bruker_id")
            handling = request.form.get("handling")
            if bruker_id and handling:
                if handling == "slett":
                    conn.execute("DELETE FROM brukere WHERE id = ?", (bruker_id,))
                    conn.execute("DELETE FROM ny_henvendelser WHERE bruker_id = ?", (bruker_id,))
                    # Obs: Dette fjerner brukeren og henvendelser knyttet til brukeren
                else:
                    ny_status = 1 if handling == "aktiver" else 0
                    conn.execute("UPDATE brukere SET aktiv = ? WHERE id = ?", (ny_status, bruker_id))
                conn.commit()

        brukere = conn.execute("SELECT * FROM brukere").fetchall()

    return render_template("rediger_brukere.htm", brukere=brukere)


    



@app.route("/loggut")
def logout():
    session.clear()
    return redirect("/logginn")

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host='0.0.0.0')
