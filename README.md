# Student Assignment Completion Predictor

## About the Project
The Student Assignment Completion Predictor is an AI-based web application designed to help teachers identify students who may be at risk of missing assignment deadlines.

It uses a Decision Tree Machine Learning algorithm to predict whether a student is likely to submit an assignment on time or may be at risk.

## Features
- Teacher Registration and Login
- Secure Password Hashing using bcrypt
- Admin Dashboard
- Student Assignment Prediction
- Attendance and Previous Submission Rate Analysis
- Assignment Deadline Tracking
- On-Time and At-Risk Predictions
- Prediction History Dashboard
- Student Performance Reports
- CSV and PDF Report Downloads
- SQLite Database Integration

## Machine Learning Model
**Algorithm:** Decision Tree Classifier

### Input Features
- Attendance Percentage
- Previous Submission Rate
- Days Remaining

### Prediction Output
- On-Time
- At-Risk

## Technologies Used
- Python
- Streamlit
- Pandas
- Scikit-learn
- SQLite
- Bcrypt
- ReportLab

## Installation and Setup

1. Clone or download this repository.
2. Open the project folder in VS Code.
3. Install the required libraries:

```bash
pip install -r requirements.txt
```

4. Run the application:

```bash
streamlit run app.py
```

5. Open the local URL displayed in the terminal.

## Project Purpose
The purpose of this project is to support teachers in monitoring assignment completion and identifying students who may need early academic reminders.

## Note
This project is developed for educational purposes. Predictions are based on the available training dataset and should be treated as decision-support estimates, not guaranteed outcomes.