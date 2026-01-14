# Scrum in Practice - Technical Introduction (Topic I)

This project is a full-stack **Distributed Shopping List application** developed for the "Scrum in Practice" Master's module at **Otto von Guericke University Magdeburg (OVGU)**.

## 📝 Project Overview
The application allows users to create and manage shopping lists that are stored locally in the browser cache, ensuring data persistence even without an internet connection. Users can synchronize their lists with a central server to generate a unique sharing ID (UUID), allowing the same list to be accessed and edited across different devices.

### Technical Requirements Fulfilled:
- **Vue.js Frontend**: A modern UI for list management.
- **Local Persistence**: Data is stored in the browser cache using Pinia.
- **Python Backend**: A Flask REST API handles global list synchronization.
- **Bootstrap Integration**: Responsive layout and styling using Bootstrap 5.

## 🔗 Live Deployment
The project is deployed and accessible at the following link:
**[https://scrum-in-practice.vercel.app/shopping-list](https://scrum-in-practice.vercel.app/shopping-list)**

---

## 🚀 Local Development Setup

Follow these steps to run the project on your local machine.

### 1. Prerequisites
- **Node.js**: Version 20.x or higher
- **pnpm**: Required package manager (`corepack enable` or `npm install -g pnpm`)
- **Python**: Version 3.x
- **Flask**: Python web framework (`pip install flask`)

---

### 2. Backend Setup (Python/Flask)

#### For macOS / Linux:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install flask
python3 app.py
```

#### Windows:
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install flask
python app.py
```

_The backend server will run at: http://127.0.0.1:5000_

### 3. Frontend Setup (Vue 3/Vite)

_These commands are the same for all Operating Systems._

#### Open a new terminal window, navigate to the frontend folder, and run:

```bash
cd frontend
# Install dependencies
pnpm install
# Start the development server
pnpm dev
```

_The frontend will be available at: http://localhost:5173_

### Tech Stack

- **Frontend:** Vue 3 (Composition API), Vite, Pinia, Bootstrap 5
- **Backend:** Python 3, Flask, SQLite3
- **Tools:** Git, pnpm, Homebrew (macOS), Powershell/CMD (Windows)