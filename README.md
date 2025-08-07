# Nomos Chatbot

Ein intelligenter Tutor-Chatbot für Studierende der politischen Philosophie (2. Semester, Universität Hamburg). Der Bot unterstützt beim eigenständigen Lernen, Essay-Entwicklung und Prüfungsvorbereitung - ohne die Arbeit für Sie zu erledigen.

## Hinweis

- Dieser Chatbot ist ein experimentelles System zu Studienzwecken.
- Die bereitgestellten Informationen können unvollständig oder fehlerhaft sein.
- Bei Prüfungen kann kein Anspruch auf Richtigkeit oder Vollständigkeit der Antworten geltend gemacht werden.
- Eingegebene Daten können mit OpenAI geteilt und zu Trainingszwecken verwendet werden. Bitte geben Sie keine sensiblen oder persönlichen Informationen ein.

## Zugang erhalten

Der Chatbot verwendet eine benutzerbasierte Authentifizierung:
- Öffnen Sie die App mit Ihrem Benutzercode: `http://nomosai.streamlit.app/?user=IHR_BENUTZERCODE`
- Ohne gültigen Benutzercode ist kein Zugriff möglich

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
