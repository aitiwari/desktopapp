import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QTextEdit, QComboBox, QPushButton, QSizePolicy
)
from PyQt5.QtGui import QIcon
import chromadb

class ChatBotWindow(QDialog):
    def __init__(self):
        super().__init__()

        # Define the path to your Chroma DB (Mocked for now)
        persistence_path = "./vectordb"
        collection_names = self.list_all_collections(persistence_path)

        self.setWindowIcon(QIcon("chat.png"))  # Ensure chat.png exists
        self.setWindowTitle("DeepC - Chatbot")
        self.setGeometry(200, 200, 400, 500)

        layout = QVBoxLayout()

        # Chat Display (Read-Only)
        self.chat_display = QTextEdit()
        self.chat_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        # Collection Dropdown
        self.collection_dropdown = QComboBox()
        self.collection_dropdown.addItems(collection_names)
        layout.addWidget(self.collection_dropdown)

        # Chat Input (Small initial height)
        self.chat_input = QTextEdit()
        self.chat_input.setPlaceholderText("Type a message...")
        self.chat_input.setFixedHeight(40)
        layout.addWidget(self.chat_input)

        # Send Button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)

        self.setLayout(layout)

    def send_message(self):
        message = self.chat_input.toPlainText().strip()
        selected_collection = self.collection_dropdown.currentText()

        if message:
            self.chat_display.append(f"<b>You:</b> {message}")
            # self.chat_display.append(f"<i>Selected Collection:</i> {selected_collection}")
            self.chat_input.clear()

            # Simulated bot response (Replace with actual AI response logic)
            self.chat_display.append("<b>Bot:</b> I'm here to help!")

    def list_all_collections(self, persistence_path):
        client = chromadb.PersistentClient(path=persistence_path)

        # List all collections in the Chroma DB
        collection_names = client.list_collections()
        return collection_names


if __name__ == "__main__":
    app = QApplication(sys.argv)  # Initialize the application
    window = ChatBotWindow()       # Create chatbot window
    window.show()                  # Show window
    sys.exit(app.exec_())           # Run the event loop
