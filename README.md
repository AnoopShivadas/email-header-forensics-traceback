<h1 align="center">Email Header Forensics & Threat Traceback Portal</h1>

<p align="center">
  <b>Advanced Email Threat Analysis & Header Intelligence Platform</b><br>
  <sub>Analyze email headers, trace IP routing paths, and detect phishing risks using structured forensic insights</sub>
</p>

---

<p align="center">
  <a href="https://email-forensics-app.onrender.com/">
    <img src="https://img.shields.io/badge/🚀 Live Demo-Explore Application-2ecc71?style=for-the-badge"/>
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Backend-Flask-black?style=flat-square&logo=flask"/>
  <img src="https://img.shields.io/badge/Frontend-HTML%20%7C%20CSS%20%7C%20JavaScript-orange?style=flat-square&logo=javascript"/>
  <img src="https://img.shields.io/badge/Database-SQLite-lightgrey?style=flat-square"/>
  <img src="https://img.shields.io/badge/Deployment-Render-00c853?style=flat-square"/>
</p>

---

<p align="center">
  <img src="https://raw.githubusercontent.com/AnoopShivadas/email-header-forensics-traceback/main/Email_GIF.gif" width="900"/>
</p>

---


## 🧠 Project Overview

The **Email Header Forensics & Threat Traceback Portal** is designed to perform structured analysis of raw email headers to uncover hidden routing paths, detect authentication failures, and trace sender origins.

This project replicates **real-world email investigation workflows** used in cybersecurity and digital forensics.

---

## ⚙️ Key Features

### 🔍 Header Parsing Engine

* Extracts `Received` chain
* Identifies sender IP addresses
* Parses timestamps and mail servers

### 🌍 IP Geolocation Tracking

* Maps IP addresses to physical locations
* Visualizes global email routing paths

### 🛡 Email Authentication Analysis

* SPF result extraction
* DKIM presence detection

### ⚠️ Risk Scoring System

* Rule-based anomaly detection
* Flags suspicious headers
* Generates risk levels

### 📊 History & Reporting

* Stores previous analyses
* Export results as CSV / PDF

### 🔐 Authentication System

* User login system
* Admin dashboard functionality

---

## 🏗 System Architecture

```mermaid
flowchart LR
    A[Email Header Input] --> B[Parser Engine]
    B --> C[IP Extraction]
    C --> D[Geo Lookup]
    B --> E[SPF/DKIM Analysis]
    D --> F[Risk Engine]
    E --> F
    F --> G[Results Dashboard]
```

---

## 🛠 Tech Stack

| Layer         | Technology            |
| ------------- | --------------------- |
| Frontend      | HTML, CSS, JavaScript |
| Backend       | Python (Flask)        |
| Database      | SQLite                |
| Visualization | JavaScript Maps       |
| Deployment    | Render                |

---

## 📂 Project Structure

```bash
backend/
├── app.py
├── parser.py
├── geo.py
├── risk.py
├── models.py
├── auth.py
├── auth_utils.py
├── static/
├── templates/
```

---

## 🚀 Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/your-username/email-forensics.git
cd email-forensics
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create `.env` file:

```env
SECRET_KEY=your_secret_key
```

### 5. Run the Application

```bash
python backend/app.py
```

---

## 🔐 Security Considerations

* Sensitive data stored using environment variables
* `.env` and secret files excluded via `.gitignore`
* No credentials exposed in repository

---

## 📈 Future Scope

* Integration with threat intelligence APIs
* Advanced anomaly detection techniques
* Cloud database (PostgreSQL)
* Enhanced analytics dashboard

---

## 👨‍💻 Author

**Anoop Shivadas**
B.Sc IT | Cybersecurity

---

## ⭐ Project Significance

This project demonstrates practical implementation of:

* Email header forensic analysis
* Threat tracing techniques
* Backend data processing
* Secure web application development

---

<p align="center">
  ⭐ Star this repository if you find it useful!
</p>
