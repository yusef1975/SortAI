# SortAI Pro 🚀
**Intelligent, Privacy-First File Organization powered by AI.**

SortAI Pro is a high-performance desktop utility that uses Large Language Models (Gemini, GPT-4o, Claude) to semantically organize your files into logical categories based on their context, not just their extension.

![Status](https://img.shields.io/badge/Status-Stable-brightgreen)
![License](https://img.shields.io/badge/License-MIT-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

---

## ✨ Features
- 🤖 **Universal AI Engine**: Supports Gemini, OpenAI, and Anthropic.
- 🏠 **Local LLM Support**: Connect to Ollama or LocalAI for 100% private, internal sorting.
- 🛰️ **Background Watcher**: Uses OS-level hooks to monitor folders with 0% idle CPU usage.
- 📜 **Activity History**: Detailed logs and one-click **Undo** functionality.
- 🔒 **Total Privacy**: **SortAI never reads file contents.** Only filenames are used for categorization.
- 🔔 **Native Notifications**: Real-time Windows alerts when files are moved.
- 🎛️ **System Tray Mode**: Runs silently in the background.

## 🚀 Installation & Usage

### 📥 Standalone Executable (Recommended)
1. Go to the [Releases](https://github.com/yusef1975/SortAI/releases) page.
2. Download `SortAI_Pro.exe`.
3. Run the application—no installation or Python required!

### 🛠️ Developer Setup (Run from Source)
1. Clone the repository:
   ```bash
   git clone https://github.com/yusef1975/SortAI.git
   cd SortAI
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python main.py
   ```

## 🛠️ Configuration
1. Open the **Settings** tab.
2. Select your **AI Company** (e.g., Gemini).
3. Paste your **API Key**.
4. Add the folders you want to monitor (e.g., `Downloads`).
5. Choose your **Organized Root** or enable **In-Place** sorting.
6. Click **Save Settings & Restart**.

## 🛡️ Security & Privacy
SortAI is a "local-first" tool:
- **No Data Harvesting**: Your API keys and configuration stay on your disk.
- **Privacy Isolation**: Decisions are made based on metadata (filenames) only.
- **Boot Safety**: Optional "Start with Windows" ensures you're protected from the moment you log in.

## 📄 License
This project is licensed under the MIT License.
