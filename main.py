from PyQt5.QtCore import QThread, pyqtSignal, QUrl, Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QToolBar, QAction, QVBoxLayout, QWidget,
    QTextEdit, QSplitter, QPushButton, QGroupBox, QCheckBox, QHBoxLayout
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from bs4 import BeautifulSoup
import markdown
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLabel, QLineEdit, QCheckBox, QVBoxLayout, QHBoxLayout, QWidget, QMainWindow, QToolBar, QPushButton, QGroupBox, QTextEdit, QSplitter, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from src.chatbot import ChatBotWindow
from src.pyautogen import Chat
from src.vectorstores.vectorstorcontent import DocumentProcessor  # Import Chat for AI processing


class AIWorker(QThread):
    """Worker thread to process AI-generated text asynchronously."""
    finished = pyqtSignal(dict)  # Signal to send back processed content

    def __init__(self, text_content):
        super().__init__()
        self.text_content = text_content

    def run(self):
        """Runs AI processing in a separate thread to prevent UI freezing."""
        obj_chat = Chat(self.text_content)
        updated_text_content = obj_chat.call_ai_agent()

        # Extract think content, summary, and other content
        processed_content = self.process_text_content(updated_text_content)

        # Emit signal with processed content
        self.finished.emit(processed_content)

    def process_text_content(self, text_content):
        """Extracts <think> and <summary> sections from text."""
        think_content = ""
        summary_content = ""
        rest_content = text_content

        # Extract <think> content
        if "<think>" in text_content and "</think>" in text_content:
            start_index = text_content.find("<think>") + len("<think>")
            end_index = text_content.find("</think>")
            think_content = text_content[start_index:end_index]
            rest_content = text_content.replace(f"<think>{think_content}</think>", "")
        
        return {
            "think_content": think_content,
            "rest_content": rest_content
        }

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("deepC.ico"))
        self.setWindowTitle("DeepC")
        self.setGeometry(100, 100, 1024, 768)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        splitter = QSplitter(Qt.Horizontal)
        central_layout = QVBoxLayout(central_widget)
        central_layout.addWidget(splitter)

        # Left Column (Text Display + Expanders)
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        splitter.addWidget(left_column)

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet("background-color: #1E1E1E; color: white; padding: 5px;")
        left_layout.addWidget(self.text_display)

        self.summary_group = QGroupBox("Summary")
        self.summary_layout = QVBoxLayout(self.summary_group)
        self.summary_button = QPushButton("Show Summary")
        self.summary_button.setCheckable(True)
        self.summary_button.clicked.connect(self.toggle_summary)
        self.summary_content_display = QTextEdit()
        self.summary_content_display.setReadOnly(True)
        self.summary_content_display.setVisible(False)
        self.summary_layout.addWidget(self.summary_button)
        self.summary_layout.addWidget(self.summary_content_display)
        left_layout.addWidget(self.summary_group)

        self.think_group = QGroupBox("Think Content")
        self.think_layout = QVBoxLayout(self.think_group)
        self.think_button = QPushButton("Show Think Content")
        self.think_button.setCheckable(True)
        self.think_button.clicked.connect(self.toggle_think_content)
        self.think_content_display = QTextEdit()
        self.think_content_display.setReadOnly(True)
        self.think_content_display.setVisible(False)
        self.think_layout.addWidget(self.think_button)
        self.think_layout.addWidget(self.think_content_display)
        left_layout.addWidget(self.think_group)

        # Right Column (Browser + Configuration)
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)

        # Web Browser
        self.browser = QWebEngineView()
        self.browser.loadFinished.connect(self.on_page_load_finished)  # Connect to page load finished signal
        right_layout.addWidget(self.browser)

        # Navigation Buttons (Back, Forward, Home, Search)
        self.nav_toolbar = QToolBar("Navigation")
        self.nav_toolbar.setStyleSheet("QToolButton { padding: 5px; border-radius: 5px; color: white; }"
                                      "QToolButton:hover { background-color: #45a049; }")
        self.back_button = QAction(QIcon("back.png"), "Back", self)
        self.back_button.triggered.connect(self.browser.back)
        self.nav_toolbar.addAction(self.back_button)

        self.forward_button = QAction(QIcon("forward.png"), "Forward", self)
        self.forward_button.triggered.connect(self.browser.forward)
        self.nav_toolbar.addAction(self.forward_button)

        self.home_button = QAction(QIcon("home.png"), "Home", self)
        self.home_button.triggered.connect(self.navigate_home)
        self.nav_toolbar.addAction(self.home_button)

        self.search_button = QAction(QIcon("search.png"), "Search", self)
        self.search_button.triggered.connect(self.navigate_search)
        self.nav_toolbar.addAction(self.search_button)
        
        self.chat_button = QAction(QIcon("chat.png"), "Chat", self)
        self.chat_button.triggered.connect(self.open_chatbot)
        self.nav_toolbar.addAction(self.chat_button)

        right_layout.addWidget(self.nav_toolbar)

        # Configuration Section
        self.config_group = QGroupBox("Configuration")
        self.config_group.setMaximumHeight(150)  # Reduced height
        self.config_layout = QVBoxLayout(self.config_group)

        # Add a checkbox inside the Configuration group box
        self.enable_search_checkbox = QCheckBox("Enable Search")
        self.enable_search_checkbox.setChecked(True)  # Set to true by default
        self.enable_search_checkbox.stateChanged.connect(self.toggle_browser_visibility)
        self.config_layout.addWidget(self.enable_search_checkbox)

        # Add a store checkbox
        self.store_checkbox = QCheckBox("Enable Store")
        self.store_checkbox.stateChanged.connect(self.on_store_checkbox_changed)  # Connect to method
        self.config_layout.addWidget(self.store_checkbox)

        # Add a text box for the collection name (Initially hidden)
        self.collection_name_label = QLabel("Collection Name:")
        self.collection_name_input = QLineEdit()
        self.collection_name_input.setPlaceholderText("Enter custom collection name")
        self.collection_name_label.setVisible(False)  # Initially hidden
        self.collection_name_input.setVisible(False)  # Initially hidden
        self.config_layout.addWidget(self.collection_name_label)
        self.config_layout.addWidget(self.collection_name_input)

        right_layout.addWidget(self.config_group)

        # Now it's safe to call navigate_home()
        self.navigate_home()

        # Show/Hide Configuration Button at Bottom
        self.config_button = QPushButton("Show Configuration")
        self.config_button.setCheckable(True)
        self.config_button.clicked.connect(self.toggle_configuration)
        right_layout.addWidget(self.config_button)

        splitter.addWidget(right_column)

    def on_store_checkbox_changed(self, state):
        """Handles the state change of the Enable Store checkbox."""
        if state == Qt.Checked:
            # Make the collection name input visible
            self.collection_name_label.setVisible(True)
            self.collection_name_input.setVisible(True)
        else:
            # Hide the collection name input and use default collection name
            self.collection_name_label.setVisible(False)
            self.collection_name_input.setVisible(False)

    def navigate_home(self):
        if self.enable_search_checkbox.isChecked():
            self.browser.setUrl(QUrl("http://www.google.com"))
            self.browser.setVisible(True)
            self.nav_toolbar.setVisible(True)  # Show navigation toolbar
        else:
            self.browser.setVisible(False)
            self.nav_toolbar.setVisible(False)  # Hide navigation toolbar

    def navigate_search(self):
        if self.enable_search_checkbox.isChecked():
            self.browser.setUrl(QUrl("http://www.google.com"))
            self.browser.setVisible(True)
            self.nav_toolbar.setVisible(True)  # Show navigation toolbar

    def toggle_browser_visibility(self):
        if self.enable_search_checkbox.isChecked():
            self.browser.setVisible(True)
            self.nav_toolbar.setVisible(True)  # Show navigation toolbar
            self.navigate_home()
        else:
            self.browser.setVisible(False)
            self.nav_toolbar.setVisible(False)  # Hide navigation toolbar

    def toggle_configuration(self):
        is_visible = self.config_button.isChecked()
        self.config_group.setVisible(is_visible)
        self.config_button.setText("Hide Configuration" if is_visible else "Show Configuration")

    def toggle_summary(self):
        is_visible = self.summary_button.isChecked()
        self.summary_content_display.setVisible(is_visible)
        self.summary_button.setText("Hide Summary" if is_visible else "Show Summary")

    def toggle_think_content(self):
        is_visible = self.think_button.isChecked()
        self.think_content_display.setVisible(is_visible)
        self.think_button.setText("Hide Think Content" if is_visible else "Show Think Content")

    def on_page_load_finished(self):
        """Callback when a web page has finished loading."""
        self.browser.page().toHtml(self.handle_html_content)

    def handle_html_content(self, html_content):
        """Handles the HTML content of the page."""
        soup = BeautifulSoup(html_content, "html.parser")
        page_text = soup.get_text()  # Extracts the text content from the page

        # Start the AI processing
        self.start_ai_processing(page_text)

    def start_ai_processing(self, text_content):
        """Starts the AI worker to process the content."""
        self.ai_worker = AIWorker(text_content)
        self.ai_worker.finished.connect(self.update_ui_with_processed_content)
        self.ai_worker.start()

    def update_ui_with_processed_content(self, processed_content):
        """Updates the UI with the AI-processed content."""
        self.think_content_display.setText(processed_content.get("think_content", ""))
        self.text_display.setText(processed_content.get("rest_content", ""))

        # If 'Enable Store' checkbox is checked, call vector_store with rest_content
        if self.store_checkbox.isChecked():
            self.vector_store(processed_content.get("rest_content", ""))

    def vector_store(self, rest_content):
        """Store the rest content."""
        model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        persist_directory = "./vectordb/"  
        # Check the collection name input and use default if empty
        collection_name = self.collection_name_input.text() if self.store_checkbox.isChecked() else 'default'
        print(f'Storing content to collection {collection_name}')  # You can replace this with actual storing logic

        document_processor = DocumentProcessor(
            model_name=model_name,
            persist_directory=persist_directory,
            collection_name=collection_name
        )
        document_processor.process_document(rest_content)
        
    def open_chatbot(self):
        self.chatbot_window = ChatBotWindow()
        self.chatbot_window.show()

app = QApplication([])
window = Browser()
window.show()
app.exec_()
