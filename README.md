# 💰 Expense Settlement App

A powerful, user-friendly web application for tracking and settling group expenses. Built with Python and Streamlit, this app helps you manage shared expenses among multiple people and automatically calculates the optimal settlement plan.

## ✨ Features

- **Easy Expense Entry**: Add expenses one at a time with a clean, intuitive form
- **Dynamic Participant Management**: Add or remove participants for each expense
- **Head Count Support**: Handle cases where one person represents multiple people (e.g., families)
- **Live Financial Summary**: Real-time overview of who paid what and who owes what
- **Automatic Settlement Calculation**: Generate optimal payment plans to clear all debts
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Built-in Help**: Comprehensive documentation accessible within the app

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation & Setup

#### macOS (Easiest)
```bash
# 1. Download/extract the project
# 2. Open Terminal in the project folder
# 3. Run automated setup
chmod +x setup_macos.sh
./setup_macos.sh

# 4. Launch the app
./run_app.sh
```

#### Windows
```bash
# 1. Download/extract the project
# 2. Open Command Prompt in the project folder
# 3. Manual setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 4. Launch the app
run_app.bat
```

#### Linux
```bash
# 1. Download/extract the project
# 2. Open Terminal in the project folder
# 3. Manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Launch the app
./run_app.sh
```

### Running the App

**Option 1: Using Launcher Scripts (Recommended)**
- **Windows**: Double-click `run_app.bat`
- **macOS/Linux**: Run `./run_app.sh`

**Option 2: Manual Launch**
```bash
# Activate virtual environment (if not already active)
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Run the app
streamlit run app.py
```

Then open your browser to `http://localhost:8501`

## 📖 How to Use

1. **Configure People**: In the sidebar, enter the names of payers and participants (comma-separated)
2. **Add Expenses**: Use the form to add expenses one by one
3. **View Summary**: Check the live financial summary to see current balances
4. **Calculate Settlement**: Generate the final payment plan

For detailed instructions, click the "❓ How to Use This App" expander in the sidebar.

## 🛠️ Technical Details

- **Framework**: Streamlit
- **Language**: Python 3.8+
- **Dependencies**: See `requirements.txt`
- **Data Storage**: Session-based (data persists during app session)

## 📁 Project Structure

```
expense-settlement/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── run_app.bat        # Windows launcher
├── run_app.sh         # macOS/Linux launcher
├── setup_macos.sh     # macOS setup automation
├── HELP.md            # User documentation
├── README.md          # This file
└── venv/              # Virtual environment (created during setup)
```

## 🔧 Troubleshooting

### Common Issues

**"Module not found" errors:**
- Make sure the virtual environment is activated
- Run `pip install -r requirements.txt` again

**Port already in use:**
- The app uses port 8501 by default
- If busy, Streamlit will automatically try the next available port

**Permission denied (macOS/Linux):**
- Make shell scripts executable: `chmod +x run_app.sh setup_macos.sh`

**Python not found:**
- Ensure Python 3.8+ is installed and in your PATH
- On macOS/Linux, you might need to use `python3` instead of `python`

### Getting Help

- Check the built-in help section in the app sidebar
- Review the `HELP.md` file for detailed usage instructions
- Ensure all dependencies are properly installed

## 🔄 Portability

This app is designed to be portable across different machines and operating systems:

- **Virtual Environment**: All dependencies are isolated
- **Platform-Specific Launchers**: Easy startup on any OS
- **Consistent Experience**: Same functionality everywhere
- **Easy Transfer**: Copy the project folder (excluding `venv/`) to any machine

## ☁️ Cloud Setup (Optional)

To enable cloud features (Sharing, Persistence, and Backups):

1.  **Create a Google Service Account**:
    -   Go to Google Cloud Console > IAM & Admin > Service Accounts
    -   Create a new service account and download the JSON key.
    -   Enable **Google Sheets API** and **Google Drive API** for your project.

2.  **Create the Database Sheet**:
    -   Go to Google Sheets and create a new blank spreadsheet.
    -   Name it exactly: **`Expense Settlement DB`**
    -   **Share** this sheet with your Service Account email (found in the JSON key) as an **Editor**.

3.  **Configure Secrets**:
    -   **Local**: Save your JSON key as `kaustavsampleproject-2dda07854172.json` in the project root.
    -   **Streamlit Cloud**: Paste the JSON content into the `GOOGLE_SERVICE_ACCOUNT` secret.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the application.

## 📄 License

This project is open source and available under the MIT License. 