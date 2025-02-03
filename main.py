from PyQt5.QtCore import QThread, pyqtSignal
import sys
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QToolBar, QAction, QVBoxLayout, QWidget, 
    QTextEdit, QSplitter, QPushButton, QGroupBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from bs4 import BeautifulSoup
import markdown

from src.pyautogen import Chat  # Import Chat for AI processing


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
        self.setWindowTitle("My Browser")
        self.setGeometry(100, 100, 1024, 768)

        # Create a central widget and set the layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Use QSplitter to create resizable left and right columns
        splitter = QSplitter(Qt.Horizontal)
        central_layout = QVBoxLayout(central_widget)
        central_layout.addWidget(splitter)

        # Left column (Text Display + Expanders)
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        splitter.addWidget(left_column)

        # Markdown Text Display
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet("background-color: #1E1E1E; color: white; padding: 5px;")
        left_layout.addWidget(self.text_display)

        # Summary Expander Section
        self.summary_group = QGroupBox("Summary")
        self.summary_layout = QVBoxLayout(self.summary_group)

        self.summary_button = QPushButton("Show Summary")
        self.summary_button.setCheckable(True)
        self.summary_button.clicked.connect(self.toggle_summary)

        self.summary_content_display = QTextEdit()
        self.summary_content_display.setReadOnly(True)
        self.summary_content_display.setVisible(False)  # Initially hidden

        self.summary_layout.addWidget(self.summary_button)
        self.summary_layout.addWidget(self.summary_content_display)
        left_layout.addWidget(self.summary_group)

        # Think Content Expander Section
        self.think_group = QGroupBox("Think Content")
        self.think_layout = QVBoxLayout(self.think_group)

        self.think_button = QPushButton("Show Think Content")
        self.think_button.setCheckable(True)
        self.think_button.clicked.connect(self.toggle_think_content)

        self.think_content_display = QTextEdit()
        self.think_content_display.setReadOnly(True)
        self.think_content_display.setVisible(False)  # Initially hidden

        self.think_layout.addWidget(self.think_button)
        self.think_layout.addWidget(self.think_content_display)
        left_layout.addWidget(self.think_group)

        # Right column (browser)
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)

        # Set up the browser
        self.browser = QWebEngineView()
        right_layout.addWidget(self.browser)

        # Navigation bar
        navtb = QToolBar("Navigation")
        right_layout.addWidget(navtb)

        # Back button
        back_btn = QAction("Back", self)
        back_btn.triggered.connect(self.browser.back)
        navtb.addAction(back_btn)

        # Forward button
        forward_btn = QAction("Forward", self)
        forward_btn.triggered.connect(self.browser.forward)
        navtb.addAction(forward_btn)

        # Reload button
        reload_btn = QAction("Reload", self)
        reload_btn.triggered.connect(self.browser.reload)
        navtb.addAction(reload_btn)

        # Home button
        home_btn = QAction("Home", self)
        home_btn.triggered.connect(self.navigate_home)
        navtb.addAction(home_btn)

        # URL bar
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        navtb.addWidget(self.urlbar)

        # Stop button
        stop_btn = QAction("Stop", self)
        stop_btn.triggered.connect(self.browser.stop)
        navtb.addAction(stop_btn)

        # Add the right column to the splitter
        splitter.addWidget(right_column)

        # Set home page
        self.navigate_home()

        # Update URL bar when the page changes
        self.browser.urlChanged.connect(self.update_urlbar)

        # Connect the loadFinished signal to extract text
        self.browser.loadFinished.connect(self.extract_text)

    def navigate_home(self):
        self.browser.setUrl(QUrl("http://www.google.com"))

    def navigate_to_url(self):
        q = QUrl(self.urlbar.text())
        if q.scheme() == "":
            q.setScheme("http")
        self.browser.setUrl(q)

    def update_urlbar(self, q):
        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)

    def extract_text(self):
        """Extract and display text using BeautifulSoup after page load."""
        self.browser.page().toHtml(self.process_html)

    def process_html(self, html):
        """Parse HTML with BeautifulSoup and start AI processing in a separate thread."""
        soup = BeautifulSoup(html, "html.parser")
        text_content = soup.get_text(separator="\n", strip=True)  # Extract readable text
        
        # Start AI processing in a separate thread
        self.worker = AIWorker(text_content)
        self.worker.finished.connect(self.display_content)
        self.worker.start()

    def display_content(self, processed_content):
        """Displays content where Think and Summary content are expandable, and the rest is in markdown."""
        # Convert rest of the content to markdown
        markdown_content = markdown.markdown(processed_content["rest_content"])  # Converts rest content to HTML

        # Update the markdown display
        self.text_display.setHtml(markdown_content)

        # Update the Summary content display
        if processed_content["rest_content"]:
            self.summary_content_display.setPlainText(processed_content["rest_content"])
            self.summary_group.setVisible(True)
        else:
            self.summary_group.setVisible(False)
        

        # Update the Think content display
        if processed_content["think_content"]:
            self.think_content_display.setPlainText(processed_content["think_content"])
            self.think_group.setVisible(True)
        else:
            self.think_group.setVisible(False)

    # def toggle_summary(self):
    #     """Toggles visibility of the summary content display."""
    #     self.summary_content_display.setVisible(self.summary_button.isChecked())
    def toggle_summary(self):
        """Toggles visibility of the summary content display."""
        is_visible = self.summary_button.isChecked()
        self.summary_content_display.setVisible(is_visible)
        self.summary_button.setText("Hide Summary" if is_visible else "Show Summary")


    def toggle_think_content(self):
        """Toggles visibility of the think content display."""
        self.think_content_display.setVisible(self.think_button.isChecked())


app = QApplication(sys.argv)
window = Browser()
window.show()
sys.exit(app.exec_())
