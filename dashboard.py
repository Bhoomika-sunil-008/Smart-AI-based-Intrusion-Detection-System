
from flask import Flask, render_template_string, send_from_directory
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "farm_history.db")
EVIDENCE_FOLDER = os.path.join(BASE_DIR, "evidence")


def get_alerts():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    alerts = conn.execute(
        "SELECT * FROM alerts ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return [
        {
            **dict(alert),
            "image_file": os.path.basename(
                alert["image_path"] or ""
            )
        }
        for alert in alerts
    ]


@app.route("/")
def home():
    alerts = get_alerts()

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta http-equiv="refresh" content="5">
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">

        <title>FarmGuard AI | Dashboard</title>

        <style>
            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f4f8f2;
                color: #24372b;
            }

            header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 25px;
                padding: 35px 6%;
                background: white;
                flex-wrap: wrap;
            }

            .intro {
                flex: 1;
                min-width: 250px;
            }

            .intro h1 {
                color: #245c3b;
                font-size: 36px;
                margin-bottom: 10px;
            }

            .intro p {
                color: #65776a;
                line-height: 1.6;
            }

            .farm-image {
                width: 42%;
                min-width: 260px;
                height: 230px;
                object-fit: cover;
                border-radius: 18px;
            }

            .status {
                display: inline-block;
                background: #e1f4e5;
                color: #23643b;
                padding: 9px 14px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: bold;
            }

            main {
                padding: 30px 6%;
            }

            .summary {
                display: grid;
                grid-template-columns:
                    repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 28px;
            }

            .card {
                background: white;
                padding: 24px;
                border-radius: 15px;
                box-shadow: 0 4px 15px #203b2010;
            }

            .card p {
                color: #738075;
                margin-bottom: 8px;
            }

            .card h2 {
                color: #245c3b;
                font-size: 32px;
                margin: 0;
            }

            .history {
                background: white;
                border-radius: 15px;
                padding: 24px;
                box-shadow: 0 4px 15px #203b2010;
                overflow-x: auto;
            }

            .history h2 {
                color: #245c3b;
            }

            .history table {
                width: 100%;
                border-collapse: collapse;
                min-width: 650px;
            }

            th, td {
                text-align: left;
                padding: 15px 12px;
                border-bottom: 1px solid #e9eee8;
            }

            th {
                background: #f0f6ef;
                color: #355b40;
            }

            .object {
                font-weight: bold;
                text-transform: capitalize;
            }

            .evidence {
                width: 100px;
                height: 70px;
                object-fit: cover;
                border-radius: 8px;
            }

            .empty {
                padding: 25px;
                text-align: center;
                color: #718073;
            }

            .refresh {
                display: inline-block;
                background: #286342;
                color: white;
                text-decoration: none;
                padding: 10px 16px;
                border-radius: 8px;
                margin-bottom: 15px;
            }

            footer {
                text-align: center;
                color: #758477;
                padding: 25px;
                font-size: 13px;
            }

            @media (max-width: 650px) {
                header {
                    padding: 25px 5%;
                }

                .intro h1 {
                    font-size: 29px;
                }

                .farm-image {
                    width: 100%;
                    min-width: 0;
                }

                main {
                    padding: 22px 5%;
                }
            }
        </style>
    </head>

    <body>
        <header>
            <div class="intro">
                <h1>🌿 FarmGuard AI</h1>

                <p>
                    AI-Based Smart Intrusion Detection System
                    for Farm
                </p>

                <span class="status">
                    ● Farm Monitoring Dashboard
                </span>
            </div>

            <img
                class="farm-image"
                src="https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1000&q=85"
                alt="Peaceful green agricultural fields"
            >
        </header>

        <main>
            <section class="summary">
                <div class="card">
                    <p>Total Intrusion Records</p>
                    <h2>{{ alerts|length }}</h2>
                </div>

                <div class="card">
                    <p>Human Detections</p>
                    <h2>
                        {{ alerts|selectattr(
                            'object_name', 'equalto', 'person'
                        )|list|length }}
                    </h2>
                </div>

                <div class="card">
                    <p>Animal Detections</p>
                    <h2>
                        {{ alerts|rejectattr(
                            'object_name', 'equalto', 'person'
                        )|list|length }}
                    </h2>
                </div>
            </section>

            <section class="history">
                <h2>Intrusion History</h2>

                <p>
                    Review recorded detections and their evidence.
                </p>

                <a class="refresh" href="/">
                    ↻ Refresh Records
                </a>

                {% if alerts %}
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Detected Object</th>
                            <th>Confidence</th>
                            <th>Date & Time</th>
                            <th>Evidence</th>
                        </tr>
                    </thead>

                    <tbody>
                        {% for alert in alerts %}
                        <tr>
                            <td>{{ alert.id }}</td>

                            <td class="object">
                                {{ alert.object_name }}
                            </td>

                            <td>
                                {{ "%.1f"|format(
                                    alert.confidence * 100
                                ) }}%
                            </td>

                            <td>{{ alert.timestamp }}</td>

                            <td>
                                {% if alert.image_file %}
                                <a
                                    href="{{ url_for(
                                        'evidence',
                                        filename=alert.image_file
                                    ) }}"
                                    target="_blank"
                                >
                                    <img
                                        class="evidence"
                                        src="{{ url_for(
                                            'evidence',
                                            filename=alert.image_file
                                        ) }}"
                                        alt="Detection evidence"
                                    >
                                </a>
                                {% else %}
                                Not available
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>

                {% else %}
                <div class="empty">
                    No intrusion records have been saved yet.
                </div>
                {% endif %}
            </section>
        </main>

        <footer>
            FarmGuard AI · Intelligent Farm Protection
        </footer>
    </body>
    </html>
    """, alerts=alerts)


@app.route("/evidence/<path:filename>")
def evidence(filename):
    return send_from_directory(EVIDENCE_FOLDER, filename)


if __name__ == "__main__":
    app.run(debug=True)
