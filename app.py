from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import os

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "evm_demo_secret_key"
)


# =========================
# DATABASE CONNECTION
# =========================

def get_db_connection():

    return mysql.connector.connect(

        host=os.environ.get(
            "MYSQLHOST",
            "localhost"
        ),

        port=int(
            os.environ.get(
                "MYSQLPORT",
                3306
            )
        ),

        user=os.environ.get(
            "MYSQLUSER",
            "root"
        ),

        password=os.environ.get(
            "MYSQLPASSWORD",
            "6619"
        ),

        database=os.environ.get(
            "MYSQLDATABASE",
            "evm_database"
        )
    )


# =========================
# HOME
# =========================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================
# VOTING PAGE
# =========================

@app.route("/vote")
def vote():

    return render_template(
        "vote.html"
    )


# =========================
# CAST VOTE
# =========================

@app.route(
    "/cast-vote",
    methods=["POST"]
)
def cast_vote():

    voter_id = request.form.get(
        "voter_id"
    )

    candidate = request.form.get(
        "candidate"
    )

    if not voter_id or not candidate:

        return render_template(
            "success.html",
            success=False,
            message="Voter ID and candidate are required."
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        # Check duplicate vote
        cursor.execute(
            """
            SELECT id
            FROM votes
            WHERE voter_id = %s
            """,
            (voter_id,)
        )

        existing_vote = cursor.fetchone()

        if existing_vote:

            return render_template(
                "success.html",
                success=False,
                message="This Voter ID has already voted."
            )

        # Find candidate
        cursor.execute(
            """
            SELECT id
            FROM candidates
            WHERE name = %s
            """,
            (candidate,)
        )

        candidate_data = cursor.fetchone()

        if not candidate_data:

            return render_template(
                "success.html",
                success=False,
                message="Candidate not found."
            )

        candidate_id = candidate_data[0]

        # Save vote
        cursor.execute(
            """
            INSERT INTO votes
            (voter_id, candidate_id)
            VALUES (%s, %s)
            """,
            (
                voter_id,
                candidate_id
            )
        )

        # Increase candidate votes
        cursor.execute(
            """
            UPDATE candidates
            SET votes = votes + 1
            WHERE id = %s
            """,
            (candidate_id,)
        )

        connection.commit()

        return render_template(
            "success.html",
            success=True,
            candidate=candidate
        )

    except mysql.connector.Error as error:

        if connection:
            connection.rollback()

        return render_template(
            "success.html",
            success=False,
            message=f"Database error: {error}"
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================
# ADMIN LOGIN PAGE
# =========================

@app.route("/admin")
def admin():

    return render_template(
        "admin.html"
    )


# =========================
# ADMIN LOGIN
# =========================

@app.route(
    "/admin-login",
    methods=["POST"]
)
def admin_login():

    username = request.form.get(
        "username"
    )

    password = request.form.get(
        "password"
    )

    if (
        username == "admin"
        and password == "admin123"
    ):

        session[
            "admin_logged_in"
        ] = True

        return redirect(
            url_for("results")
        )

    return render_template(
        "admin.html",
        error="Invalid username or password"
    )


# =========================
# RESULTS
# =========================

@app.route("/results")
def results():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin")
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, name, votes
            FROM candidates
            ORDER BY votes DESC
            """
        )

        candidates = cursor.fetchall()

        return render_template(
            "results.html",
            candidates=candidates
        )

    except mysql.connector.Error as error:

        return f"Database error: {error}"

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )