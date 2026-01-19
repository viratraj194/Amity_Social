<div align="center">
  <h1>🤝 Amity Social</h1>
  <p><strong>A Privacy-First Anonymous Social Networking Platform</strong></p>

  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" />
  <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" />
</div>

---

## 📖 Project Overview
**Amity Social** is a social platform built to allow users to interact, share, and communicate without the pressure of traditional social media identities. The core of the project is its **Anonymous Messaging System**, which allows users to express their thoughts and connect with others while maintaining total privacy.

## 🚀 Key Functionalities
- 🕵️ **Total Anonymity:** Built-in systems to ensure messaging and interactions can remain anonymous.
- 💬 **Private Messaging:** A robust peer-to-peer messaging system for direct connections.
- 📑 **Social Feed:** Share updates and view community posts in a clean, Django-rendered interface.
- 🗄️ **Relational Architecture:** Powered by **PostgreSQL** for high-performance data handling and secure user management.
- 🔐 **Secure Auth:** Custom user authentication logic handled through Django’s secure framework.

---

## 🛠 Tech Stack & Architecture

### Backend & Logic
- **Python/Django:** Handles the Model-Template-View (MTV) architecture.
- **Django ORM:** Manages complex relationships between users, posts, and anonymous threads.

### Database
- **PostgreSQL:** Used for its reliability and advanced querying capabilities, ensuring that message data is stored and retrieved efficiently.

### Frontend
- **HTML5 & CSS3:** Clean, custom-styled templates providing a distraction-free user experience.

---

## ⚙️ How It Works (The Core Logic)
1. **The Anonymous Layer:** When a user sends a message, the system can detach the User ID from the display name, using a unique session-based or token-based identifier to mask the sender's true identity from the recipient.
2. **Database Integrity:** PostgreSQL handles the `Foreign Key` relationships between the `Messages` and `Threads` tables, ensuring that even if a user is anonymous, the data remains consistent and threaded correctly.
3. **Template Rendering:** Django’s templating engine dynamically renders anonymous vs. public content based on user-defined privacy settings.

---

## 🚀 Installation & Setup

### 1. Clone the Project
```bash
git clone [https://github.com/viratraj194/Amity_Social.git](https://github.com/viratraj194/Amity_Social.git)
cd Amity_Social
