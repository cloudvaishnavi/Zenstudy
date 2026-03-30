# ZenStudy 📚
**AI-Powered Personal Study Tracker**

ZenStudy is a comprehensive analytics dashboard and habit tracker built with Streamlit. It uses machine learning models to predict distraction likelihood and calculate focus scores, providing insightful analytics for students and lifelong learners.

![ZenStudy Dashboard](https://via.placeholder.com/800x400?text=ZenStudy+Dashboard)

## 🚀 Features
- **Study Session Logging:** Track subjects, techniques, duration, mood, and productivity.
- **AI Insights:** Automated focus score calculation and distraction prediction.
- **Rich Analytics:** Interactive Plotly charts for tracking weekly goals and studying consistency.
- **Authentication:** Custom OTP-based email verification and secure password hashing.
- **Dark & Light Mode:** Fully cohesive custom CSS theme optimized for both desktop and mobile.
- **Admin Panel:** Powerful backend analytics for app administrators.

## 🛠️ Tech Stack
- **Frontend / Fullstack Framework:** Streamlit
- **Database:** SQLite & SQLAlchemy (ORM)
- **Data Processing:** Pandas, NumPy
- **Machine Learning:** Scikit-Learn, Joblib
- **Data Visualization:** Plotly

## 💻 Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/zenstudy.git
   cd zenstudy
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Create a `.env` file in the root directory.
   - Example `.env`:
     ```env
     OWNER_EMAIL=your_email@example.com
     ```

5. **Run the application:**
   ```bash
   streamlit run app.py
   ```

## 🐳 Running with Docker

You can easily containerize and run the application using Docker.

```bash
docker build -t zenstudy .
docker run -p 8501:8501 zenstudy
```

Then open `http://localhost:8501` in your browser.

## 🧪 Testing

To run the full suite of unit tests, use Pytest:
```bash
pytest
```

## 📜 License
[MIT License](LICENSE)
