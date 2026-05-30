DARK_STYLE = """
QWidget {
    background: #15171c;
    color: #f0f3f7;
    font-family: "Segoe UI";
    font-size: 10pt;
}

QMainWindow {
    background: #15171c;
}

QLabel#TitleLabel {
    font-size: 18pt;
    font-weight: 700;
}

QLabel#StatusLabel {
    color: #9fb0c7;
}

QListWidget, QPlainTextEdit, QComboBox {
    background: #1d2027;
    border: 1px solid #303643;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #345d9d;
}

QListWidget::item {
    min-height: 28px;
    padding: 5px;
}

QListWidget::item:selected {
    background: #345d9d;
    border-radius: 4px;
}

QPushButton {
    background: #2c67c8;
    border: 0;
    border-radius: 6px;
    padding: 8px 12px;
    color: #ffffff;
    font-weight: 600;
}

QPushButton:hover {
    background: #3976dc;
}

QPushButton:pressed {
    background: #24549f;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
}

QGroupBox {
    border: 1px solid #303643;
    border-radius: 8px;
    margin-top: 12px;
    padding: 10px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
"""
