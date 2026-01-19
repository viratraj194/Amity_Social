<div align="center">
  <h1>🎭 Amity Social</h1>
  <p><strong>A Truly Anonymous Space for Unfiltered Expression</strong></p>

  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" />
  <img src="https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white" />
</div>

---

## 🌟 What is Amity Social?
**Amity Social** is designed to solve one major problem: *The Fear of Judgment.* Unlike traditional social media where every post is tied to your identity, career, and family, Amity is **100% anonymous**. Users can share thoughts, secrets, and feedback without anyone ever knowing who they are. It’s a platform built for freedom of speech in its purest form.

## 🚀 Key Features
- 🕵️ **Complete Anonymity:** No public profiles, no real names. Every interaction is designed to keep the user invisible.
- ✉️ **Anonymous Messaging System:** Send and receive messages without revealing your identity.
- ⚡ **Real-time Interaction:** Powered by **jQuery & AJAX** for a fast, seamless experience without constant page refreshes.
- 🔐 **Robust Backend:** A secure **Django** core that manages complex anonymous logic while keeping data structured.
- 📊 **Reliable Storage:** Uses **PostgreSQL** to handle message threading and user content with industrial-grade stability.

---

## ⚙️ How It Works (The Core Logic)

### 1. The Anonymity Engine
The website logic is built to strip away identifying markers. Whether you are posting on the feed or sending a direct message, the **Django backend** handles the request using unique session tokens rather than public-facing usernames.

### 2. Frontend Agility (JS & jQuery)
To keep the site feeling modern and "live," I used **jQuery AJAX** calls. 
- **Dynamic Posting:** Messages appear instantly without a full page reload.
- **Async Updates:** The message system checks for new anonymous replies in the background, making the chat feel like a real-time conversation.

### 3. The PostgreSQL Powerhouse
While the frontend is anonymous, the database is highly organized. **PostgreSQL** handles:
- Relational mapping of anonymous message threads.
- Efficient querying for the social feed using Django's ORM.

---

## 🛠 Tech Stack
- **Backend:** Python / Django
- **Database:** PostgreSQL
- **Frontend:** HTML5, CSS3, JavaScript
- **Libraries:** jQuery (for AJAX and DOM manipulation)

---

## 🚀 Installation

1. **Clone & Enter:**
   ```bash
   git clone [https://github.com/viratraj194/Amity_Social.git](https://github.com/viratraj194/Amity_Social.git)
   cd Amity_Social
