import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QTextEdit, QComboBox, QPushButton, QSizePolicy, QSplitter, QWidget, QHBoxLayout, QLabel
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import chromadb

from src.rag.contentrag import rag_chat_content

class ChatBotWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.persistence_path = "./vectordb"
        self.collection_names = self.list_all_collections(self.persistence_path)
        self.mode = "websearch"  # Default mode

        self.setWindowIcon(QIcon("chat.png"))
        self.setWindowTitle("startstruck - Chatbot")
        self.setGeometry(200, 200, 600, 500)

        main_layout = QVBoxLayout()

        # Top bar layout for toggle button
        top_bar_layout = QHBoxLayout()
        self.toggle_sidebar_button = QPushButton("☰")
        self.toggle_sidebar_button.setFixedSize(30, 30)
        self.toggle_sidebar_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.toggle_sidebar_button.clicked.connect(self.toggle_sidebar)
        top_bar_layout.addWidget(self.toggle_sidebar_button)
        top_bar_layout.addStretch()
        
        main_layout.addLayout(top_bar_layout)

        self.splitter = QSplitter(Qt.Horizontal)

        # Sidebar widget
        self.sidebar = QWidget()
        self.sidebar.setMinimumWidth(150)
        self.sidebar.setMaximumWidth(300)
        sidebar_layout = QVBoxLayout()

        # WebSearch and Web Automation Buttons
        self.websearch_button = QPushButton("🌍 WebSearch")
        self.websearch_button.clicked.connect(lambda: self.switch_mode("websearch"))
        sidebar_layout.addWidget(self.websearch_button)

        self.webautomation_button = QPushButton("⚙️ Web Automation")
        self.webautomation_button.clicked.connect(lambda: self.switch_mode("webautomation"))
        sidebar_layout.addWidget(self.webautomation_button)

        sidebar_layout.addStretch()
        self.sidebar.setLayout(sidebar_layout)
        self.splitter.addWidget(self.sidebar)
        self.sidebar.hide()

        # Main content widget
        self.main_content = QWidget()
        main_content_layout = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.chat_display.setReadOnly(True)
        main_content_layout.addWidget(self.chat_display)

        self.collection_dropdown = QComboBox()
        self.collection_dropdown.addItems(self.collection_names)
        main_content_layout.addWidget(self.collection_dropdown)

        self.chat_input = QTextEdit()
        self.chat_input.setPlaceholderText("Type a message...")
        self.chat_input.setFixedHeight(40)
        main_content_layout.addWidget(self.chat_input)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        main_content_layout.addWidget(self.send_button)

        self.main_content.setLayout(main_content_layout)
        self.splitter.addWidget(self.main_content)

        main_layout.addWidget(self.splitter)
        self.setLayout(main_layout)

    def send_message(self):
        message = self.chat_input.toPlainText().strip()

        if message:
            self.chat_display.append(f"<b>You🧑‍💻:</b> {message}")
            self.chat_input.clear()
            
            if self.mode == "websearch":
                selected_collection = self.collection_dropdown.currentText()
                response = rag_chat_content(message, selected_collection)
            else:
                if message =='Hi' or message=='hello':
                    response = "Hello 🤩, from Web Automation!"
            
            self.chat_display.append(f"<b>Bot🤖:</b> {response}")
            self.chat_display.append("---")

    def list_all_collections(self, persistence_path):
        client = chromadb.PersistentClient(path=persistence_path)
        collections = client.list_collections()
        return [collection.name for collection in collections]

    def toggle_sidebar(self):
        if self.sidebar.isVisible():
            self.sidebar.hide()
            self.toggle_sidebar_button.setText("✕")
        else:
            self.sidebar.show()
            self.toggle_sidebar_button.setText("☰")

    def switch_mode(self, mode):
        self.mode = mode
        if mode == "webautomation":
            self.collection_dropdown.hide()
        else:
            self.collection_dropdown.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatBotWindow()
    window.show()
    sys.exit(app.exec_())
