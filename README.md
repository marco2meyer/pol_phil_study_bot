# Nomos Chatbot

Ein intelligenter Tutor-Chatbot für Studierende der politischen Philosophie (2. Semester, Universität Hamburg). Der Bot unterstützt beim eigenständigen Lernen, Essay-Entwicklung und Prüfungsvorbereitung - ohne die Arbeit für Sie zu erledigen.

## Hinweis

- Dieser Chatbot ist ein experimentelles System zu Studienzwecken.
- Die bereitgestellten Informationen können unvollständig oder fehlerhaft sein.
- Bei Prüfungen kann kein Anspruch auf Richtigkeit oder Vollständigkeit der Antworten geltend gemacht werden.
- Eingegebene Daten können mit OpenAI geteilt und zu Trainingszwecken verwendet werden. Bitte geben Sie keine sensiblen oder persönlichen Informationen ein.

## Zugang erhalten

Der Chatbot verwendet jetzt eine E-Mail/Passwort-Anmeldung über Supabase Auth:
- Erstellen Sie ein Konto mit Ihrer Universitäts-E-Mail (`@uni-hamburg.de` oder `@studium.uni-hamburg.de`) und einem Passwort.
- Alternativ sind vorab freigeschaltete E-Mail-Adressen zugelassen (Whitelist).
- Bestätigen Sie Ihre E-Mail über den Link, den wir Ihnen zusenden.
- Falls Sie Ihr Passwort vergessen haben, können Sie es per E-Mail zurücksetzen.

Nach der Anmeldung werden Sie gefragt, ob Ihre Gespräche anonymisiert für Forschungszwecke ausgewertet werden dürfen. Es werden keine personenbezogenen oder identifizierbaren Informationen weitergegeben. Ihre Entscheidung (Ja/Nein) wird gespeichert und kann jederzeit geändert werden.

## Grundprinzipien

Der Chatbot ist als **fordernder Tutor** konzipiert, der Sie zum eigenständigen Denken anleitet. Er wird:
- ✅ Fragen stellen, die Sie zum Nachdenken bringen
- ✅ Feedback zu Ihren Entwürfen geben
- ✅ Begriffe aus der Pflichtlektüre erklären
- ❌ **Nicht** ganze Textabschnitte für Sie schreiben
- ❌ **Nicht** fertige Essays oder Einleitungen liefern

## 📝 Konkrete Anwendungsfälle & Prompt-Beispiele

### 1. Essay-Entwicklung

**Situation:** Sie müssen einen Essay für die Klausur schreiben, wissen aber nicht, wo Sie anfangen sollen.

**Gute Prompts:**
```
"Ich soll einen Essay zur Frage schreiben: 'Rechtfertigt das Schadensprinzip die COVID-Lockdowns in Deutschland?' Kannst du mir helfen, eine These zu entwickeln?"

"Ich habe eine Gliederung für meinen Hobbes/Locke-Essay. Kannst du schauen, ob die Struktur logisch ist?"

"Wie kann ich ein starkes Gegenargument zu meiner These formulieren, ohne meine Position zu schwächen?"
```

**Weniger hilfreiche Prompts:**
```
❌ "Schreib mir eine Einleitung zum Thema Gerechtigkeit"
❌ "Gib mir drei fertige Argumente für Rawls"
```

Abre probieren Sie es es gern aus!

### 2. Textverständnis & Begriffserklärung

**Gute Prompts:**
```
"Was meint Rawls genau mit dem 'Differenzprinzip'? Ich verstehe den Unterschied zur Gleichheit nicht."

"Kannst du mir Mills Schadensprinzip anhand eines konkreten Beispiels erklären?"

"Wie unterscheiden sich Hobbes' und Lockes Vorstellungen vom Naturzustand?"
```

### 3. Feedback zu Entwürfen

**So reichen Sie Texte ein:**
```
"Hier ist mein Essayentwurf. Bitte gib mir Feedback! Besonders unsicher bin ich bei...

[Ihr Text hier einfügen]"
```

**Der Bot wird analysieren:**
- Klarheit und Präzision Ihrer Argumente
- Logische Struktur
- Inhaltliche Richtigkeit
- Verbesserungsvorschläge (ohne Umformulierungen zu liefern)

### 4. Prüfungsvorbereitung

**Quiz-Anfragen:**
```
"Kannst du mir ein paar Multiple-Choice-Fragen zu Nozicks Libertarismus stellen?"

"Teste mein Verständnis der vier Grundfragen der politischen Philosophie"

"Stelle mir Verständnisfragen zu der heutigen Vorlesung über Menschenrechte"
```

## 🎯 Spezielle Funktionen

### Gesprächsverwaltung
- **Neue Unterhaltung:** Für jedes neue Thema/jeden neuen Essay
- **Verlauf:** Alle Gespräche werden gespeichert und sind über die Seitenleiste zugänglich
- **Feedback-System:** Bewerten Sie die Antworten des Bots. Ihr Feedback ist sehr wertvoll für die Weiterentwicklung des Chatbots.

## 💡 Tipps für bessere Ergebnisse

### Do's:
- **Seien Sie spezifisch:** "Hilf mir bei der Gliederung meines Rawls-Essays" statt "Erkläre Gerechtigkeit"
- **Stellen Sie Nachfragen:** Der Bot gibt bewusst nur schrittweise Hilfe
- **Bringen Sie eigene Ideen ein:** "Ich denke, dass... Ist das richtig?"
- **Nutzen Sie konkrete Beispiele:** "Wie würde das bei der Impfpflicht aussehen?"

### Don'ts:
- **Keine Erwartung von Bewertungen:** Der Bot kann keine Noten vergeben

## 🔍 Beispiel-Gesprächsverläufe

### Szenario: Essay-Coaching
```
Student: "Ich soll über Sicherheitsverwahrung schreiben. Hobbes vs. Locke. Keine Ahnung, wie ich anfangen soll."

Bot: "Gute Frage! Lass uns systematisch vorgehen. Hast du die Textstellen zu Hobbes' und Lockes Staatsverständnis gelesen?"

Student: "Ja, aber ich verstehe nicht, wie sich das auf Sicherheitsverwahrung anwenden lässt."

Bot: "Denk an die Grundfrage: Wofür ist der Staat da? Was würde Hobbes als Hauptaufgabe des Staates sehen?"

Student: "Sicherheit und Schutz vor dem Naturzustand?"

Bot: "Genau! Und wie könnte das die Sicherheitsverwahrung rechtfertigen? Welche Gegenposition würde Locke einnehmen?"
```

## 🛠️ Technische Hinweise

- **Sitzungen:** Ihre Gespräche bleiben erhalten, auch wenn Sie die App schließen. Sie können den Sitzungen individuelle Namen geben, wenn Sie möchten.
- **Datenschutz:** Alle Daten werden verschlüsselt in einer Datenbank gespeichert. Wir verwenden AI-Modelle von OpenAI, die von Ihnen eingegebenen Daten können von OpenAI zu Trainingszwecken verwendet werden.

## 📚 Weiterführende Ressourcen

- **Tutorien:** Der Bot ersetzt nicht die Diskussion mit Tutor*innen Kommiliton*innen.
- **Sprechstunden:** Bei grundlegenden Verständnisproblemen wenden Sie sich an die Dozierenden

## 🆘 Häufige Probleme

**"Der Bot schreibt nicht für mich"**
→ Das ist Absicht! Er soll Sie zum eigenständigen Denken anleiten.

**"Die Antworten sind zu kurz"**
→ Stellen Sie Nachfragen! Der Bot gibt bewusst schrittweise Hilfe.

**"Ich bekomme keine konkreten Beispiele"**
→ Fragen Sie spezifisch: "Kannst du das an einem Beispiel erklären?"

**"Der Bot kennt aktuelle Ereignisse nicht"**
→ Beschreiben Sie den Sachverhalt kurz, dann kann er philosophische Theorien darauf anwenden.

---

**Viel Erfolg beim Lernen!** 🎓

*Bei technischen Problemen oder Feedback wenden Sie sich an: marco.meyer@uni-hamburg.de*

---

# Betreiber:innen-Handbuch – Deployment & Betrieb

Diese Abschnitte richten sich an Administrator:innen. Sie beschreiben, wie Sie eine neue Bot-Instanz anlegen, lokal testen und auf den Server (Hetzner) mit Reverse Proxy (Nginx) und HTTPS (Let’s Encrypt) ausrollen.

## 1) Projektstruktur (Multi‑Bot)

- __Pro Bot__ ein Ordner unter `bots/<bot_name>/` mit:
  - `app.py` (Streamlit App)
  - `config.py` (Bot‑Konfiguration)
  - `.env.local` (lokal) und `.env.server` (Server; wird nicht eingecheckt)
  - `requirements.txt` (Python‑Deps nur für diesen Bot)
  - `rag/` (RAG‑Assets: `ingest_literature.py`, `rag_manifest.csv`, Vektorstore‑Helfer)
- __Container__: Generischer Streamlit‑Dockerfile unter `docker/Streamlit.Dockerfile`.
- __Compose__: `docker-compose.yml` enthält gemeinsamen Mongo‑Service und pro Bot einen Service.

## 2) Neue Bot‑Instanz anlegen

1. __Ordner kopieren__: Duplizieren Sie einen bestehenden Bot, z. B. `bots/phil_bot/` → `bots/<neuer_bot>/` und passen Sie Namen und Texte an.
2. __Env‑Dateien__:
   - `.env.local`: lokale Laufzeit (API Keys etc.)
   - `.env.server`: Server‑Laufzeit. Enthält auch `BASE_URL_PATH=<pfad_ohne_slash>`, z. B. `phil_bot`.
3. __RAG vorbereiten__ (optional): Füllen Sie `rag/rag_manifest.csv`, legen Sie PDFs ab und führen Sie die Ingestion lokal aus:
   ```bash
   cd bots/<neuer_bot>/rag
   python ingest_literature.py
   ```
4. __requirements.txt__ prüfen: nur bot‑spezifische Pakete.

## 3) Wichtige Umgebungsvariablen

- `BASE_URL_PATH` – Sub‑URL, unter der die App erreichbar ist (ohne führenden Slash), z. B. `phil_bot`.
- Supabase: `SUPABASE_URL`, `SUPABASE_ANON_KEY`
- Mongo: `MONGODB_URI` (intern: auf den Compose‑Service `mongo` zeigen) und pro Bot eigene DB‑Namen.
- OpenAI: `OPENAI_API_KEY`, Modell/Embeddings nach Bedarf.

## 4) Lokaler Test

```bash
streamlit run bots/<neuer_bot>/app.py --server.baseUrlPath=/<BASE_URL_PATH>
```

## 5) Deployment – Server vorbereiten

1. __Server Bootstrap__ (einmalig): Docker & Compose, Nginx etc. installieren. Falls nicht vorhanden, Skript `scripts/server_bootstrap.sh` verwenden/ergänzen.
2. __Deployment‑Script__: `scripts/deploy.sh` kann gezielt einen Bot bauen und deployen. Beispiel:
   ```bash
   ./scripts/deploy.sh hetzner_study_bot <neuer_bot>
   ```
   Das Skript kopiert `.env` (Root) und `bots/<neuer_bot>/.env.server` auf den Server, baut das Image über `docker/Streamlit.Dockerfile` und startet die Container via `docker-compose.yml`.

## 6) Docker Compose – zentrale Punkte

- Pro Bot‑Service Port‑Mapping wie z. B. `"127.0.0.1:8511:8501"` (empfohlen: nur localhost binden, der Reverse Proxy übernimmt den externen Zugriff).
- Build‑Args verweisen auf das per‑Bot `requirements.txt`.
- Environment im Service lädt die per‑Bot `.env.server`.

## 7) Nginx Reverse Proxy (Sub‑URL + WebSockets)

Ziel: Zugriff ohne Port, z. B. `https://example.org/<BASE_URL_PATH>/`.

Beispiel‑Serverblock (vereinfacht), Datei `/etc/nginx/sites-available/pol_phil_study_bot`:

```nginx
server {
  listen 80;
  server_name <SERVER_IP> example.org www.example.org;

  # optional: Root‑Redirect
  location = / { return 302 /<BASE_URL_PATH>/; }

  location /<BASE_URL_PATH>/ {
    proxy_pass         http://127.0.0.1:8511/<BASE_URL_PATH>/;
    proxy_set_header   Host              $host;
    proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header   Upgrade $http_upgrade;
    proxy_set_header   Connection "upgrade";
  }

  location /<BASE_URL_PATH>/stream {
    proxy_pass         http://127.0.0.1:8511/<BASE_URL_PATH>/stream;
    proxy_http_version 1.1;
    proxy_set_header   Upgrade $http_upgrade;
    proxy_set_header   Connection "upgrade";
    proxy_set_header   Host $host;
  }
}
```

Aktivieren, testen, neuladen:

```bash
ln -sf /etc/nginx/sites-available/pol_phil_study_bot /etc/nginx/sites-enabled/pol_phil_study_bot
nginx -t && systemctl reload nginx
```

## 8) DNS & HTTPS (Let’s Encrypt)

1. __DNS__: 
   - A @ → öffentliche Server‑IP (z. B. `91.99.128.203`)
   - CNAME www → Ihre Root‑Domain
   - IPv6/AAAA nur, wenn der Server IPv6 bereitstellt
2. __Certbot__ (nach DNS‑Propagation):
   ```bash
   apt-get install -y certbot python3-certbot-nginx
   certbot --nginx -d example.org -d www.example.org --redirect \
           --agree-tos -m admin@example.org --non-interactive
   ```
   Nginx wird automatisch für TLS (Port 443) konfiguriert und HTTP→HTTPS weitergeleitet.

## 9) Sicherheit & Betrieb

- __Port‑Härtung__: Bot‑Container nur an `127.0.0.1` binden; extern nur Nginx.
- __Updates__: Images regelmäßig neu bauen, Sicherheitsupdates einspielen.
- __Logs__: `docker compose logs -f <service>` und Nginx‑Logs prüfen (`/var/log/nginx/`).
- __Backups__: MongoDB‑Backups für produktive Datenbanken einplanen.

## 10) Kurzübersicht – neue Instanz in 10 Schritten

1. `bots/<neuer_bot>/` anlegen/kopieren.
2. `.env.local` und `.env.server` setzen (`BASE_URL_PATH` nicht vergessen).
3. `requirements.txt` prüfen/erweitern.
4. RAG‑Ingestion lokal ausführen (falls benötigt).
5. Compose‑Service für neuen Bot ergänzen (Port lokal binden: `127.0.0.1:x:8501`).
6. `./scripts/deploy.sh <server_alias> <neuer_bot>` ausführen.
7. Nginx‑Serverblock erstellen/aktivieren (Sub‑URL + WebSockets).
8. DNS A/CNAME setzen, warten bis auf Server IP zeigt.
9. Certbot für HTTPS ausführen, HTTP→HTTPS aktivieren.
10. Testen: `https://<domain>/<BASE_URL_PATH>/`.
