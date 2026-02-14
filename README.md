# SortAI Pro 🚀

**Intelligent, Privacy-First File Organization using AI.**

SortAI Pro is a powerful, automated file organizer that uses Large Language Models (Gemini, GPT-4o, Claude) to semantically sort your files into logical folders based on their names.

![Status](https://img.shields.io/badge/Status-Beta-orange)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## ✨ Features

- 🤖 **Universal AI Support**: Use Gemini, OpenAI, Claude, or any provider via OpenRouter/LiteLLM.
- 📁 **Multi-Folder Watching**: Monitor multiple folders (Downloads, Desktop, etc.) simultaneously.
- 📜 **Activity History**: View a detailed log of every file moved in the "History" tab.
- 🏷️ **Custom Rules**: Define your own categories or let the AI decide automatically.
- 🔒 **Privacy Focused**: **SortAI never reads your file contents.** Only filenames are used for categorization.
- 🔔 **Desktop Notifications**: Get real-time alerts when files are organized.
- 🎛️ **System Tray Integration**: Runs quietly in the background.

## 🚀 Getting Started

### Option 1: Standalone Executable (Recommended)
1. Download the latest `SortAI.exe` from the [Releases](https://github.com/USER/SortAI/releases) page.
2. Run the application. No installation required!

### Option 2: Running from Source
1. Clone the repository:
   ```bash
   git clone https://github.com/USER/SortAI.git
   cd SortAI
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## 🛠️ Configuration
1. Open the **Settings** tab.
2. Enter your **AI API Key**.
3. Add folders you want to watch.
4. Set an **Organized Root** folder where files should be moved.
5. Hit **Save Settings & Restart**.

## 🔒 Security & Privacy
SortAI is designed with security in mind:
- **No Content Access**: The software only reads filenames. Your private data inside files is never accessed or sent to any API.
- **Local Storage**: Your configuration and history are stored locally on your machine.
- **Encrypted Transmission**: AI calls are made over secure HTTPS connections.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
