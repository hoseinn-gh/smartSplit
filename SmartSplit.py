import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget,
    QInputDialog, QMessageBox, QDialog, QFormLayout, QComboBox,
    QListWidgetItem, QDialogButtonBox, QDoubleSpinBox, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QColor
import sys
import os

DATA_FILE = "split_data.json"

class Person:
    def __init__(self, name, balance=0.0):
        self.name = name
        self.balance = balance

    def to_dict(self):
        return {"name": self.name, "balance": self.balance}

    @staticmethod
    def from_dict(d):
        return Person(d["name"], d["balance"])

class SplitCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Split Calculator")
        self.resize(500, 400)

        self.people = []

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Buttons
        self.add_person_btn = QPushButton("Add Person(s)")
        self.add_expense_btn = QPushButton("Add Expense")
        self.edit_balance_btn = QPushButton("Edit Balance")
        self.save_btn = QPushButton("Save Data")

        # Add buttons to layout
        self.layout.addWidget(self.add_person_btn)
        self.layout.addWidget(self.add_expense_btn)
        self.layout.addWidget(self.edit_balance_btn)
        self.layout.addWidget(self.save_btn)

        # List widget for people
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        # Connect signals
        self.add_person_btn.clicked.connect(self.add_person)
        self.add_expense_btn.clicked.connect(self.add_expense)
        self.edit_balance_btn.clicked.connect(self.edit_balance)
        self.save_btn.clicked.connect(self.save_data)

        self.load_data()
        self.refresh_list()

        self.apply_styles()
        self.apply_glow_effects()

    def apply_styles(self):
        # Futuristic blue-purple theme - no box-shadow in stylesheet
        self.setStyleSheet("""
            QWidget {
                background-color: #0d0d1a;
                color: #d0d0ff;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 14px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6a5acd, stop:1 #00bfff);
                color: white;
                border-radius: 10px;
                padding: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #483d8b, stop:1 #1e90ff);
            }
            QListWidget {
                background-color: #12122b;
                border: 1px solid #3a3a6e;
                border-radius: 8px;
                padding: 6px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #3a3a6e;
            }
            QListWidget::item:selected {
                background-color: #7b68ee;
                color: #0d0d1a;
                font-weight: 700;
            }
            QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
                background-color: #1a1a40;
                border: 2px solid #4b0082;
                border-radius: 8px;
                padding: 6px;
                color: #b0b0ff;
                font-weight: 600;
                selection-background-color: #9370db;
                selection-color: #000000;
            }
            QComboBox::drop-down {
                border: none;
            }
            QDialog {
                background-color: #0d0d1a;
                color: #d0d0ff;
            }
            QDialogButtonBox QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7b68ee, stop:1 #00bfff);
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                font-weight: 700;
            }
            QDialogButtonBox QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6a5acd, stop:1 #1e90ff);
            }
        """)

    def apply_glow_effects(self):
        # Add glow drop shadows to main buttons
        glow_color = QColor(0, 191, 255)  # Electric blue glow

        for button in [self.add_person_btn, self.add_expense_btn, self.edit_balance_btn, self.save_btn]:
            effect = QGraphicsDropShadowEffect()
            effect.setBlurRadius(20)
            effect.setColor(glow_color)
            effect.setOffset(0)
            button.setGraphicsEffect(effect)

    def refresh_list(self):
        self.list_widget.clear()
        for p in self.people:
            item = QListWidgetItem(f"{p.name}: {p.balance:.2f}")
            self.list_widget.addItem(item)

    def add_person(self):
        names, ok = QInputDialog.getText(self, "Add Person(s)", "Enter names separated by commas:")
        if ok and names.strip():
            for name in names.split(","):
                name = name.strip()
                if name:
                    self.people.append(Person(name))
            self.refresh_list()

    def add_expense(self):
        if len(self.people) < 2:
            QMessageBox.warning(self, "Not Enough People", "Add at least 2 people first!")
            return

        dialog = ExpenseDialog(self.people, self)
        if dialog.exec():
            payer_index, amount, beneficiaries_indices = dialog.get_result()
            self.people[payer_index].balance += amount
            split_amount = amount / len(beneficiaries_indices)
            for i in beneficiaries_indices:
                self.people[i].balance -= split_amount
            self.refresh_list()

    def edit_balance(self):
        if not self.people:
            QMessageBox.warning(self, "No People", "Add people first!")
            return

        dialog = EditBalanceDialog(self.people, self)
        if dialog.exec():
            self.refresh_list()

    def save_data(self):
        data = [p.to_dict() for p in self.people]
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
        QMessageBox.information(self, "Saved", "Data saved successfully.")

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    self.people = [Person.from_dict(d) for d in data]
            except Exception as e:
                print("Failed to load data:", e)

class ExpenseDialog(QDialog):
    def __init__(self, people, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Expense")

        self.people = people

        layout = QFormLayout(self)

        self.payer_combo = QComboBox()
        for p in people:
            self.payer_combo.addItem(p.name)
        layout.addRow("Who paid?", self.payer_combo)

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMinimum(0.01)
        self.amount_input.setMaximum(1000000)
        self.amount_input.setPrefix("$ ")
        self.amount_input.setDecimals(2)
        layout.addRow("Amount paid", self.amount_input)

        self.beneficiaries_combo = QListWidget()
        self.beneficiaries_combo.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for p in people:
            item = QListWidgetItem(p.name)
            item.setSelected(True)
            self.beneficiaries_combo.addItem(item)
        layout.addRow("Who benefited? (select one or more)", self.beneficiaries_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_result(self):
        payer_index = self.payer_combo.currentIndex()
        amount = self.amount_input.value()
        beneficiaries_indices = []
        for i in range(self.beneficiaries_combo.count()):
            if self.beneficiaries_combo.item(i).isSelected():
                beneficiaries_indices.append(i)
        if not beneficiaries_indices:
            beneficiaries_indices = list(range(len(self.people)))  # fallback: all
        return payer_index, amount, beneficiaries_indices

class EditBalanceDialog(QDialog):
    def __init__(self, people, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Balances")
        self.people = people
        self.layout = QFormLayout(self)

        self.balance_edits = []
        for i, p in enumerate(people):
            edit = QDoubleSpinBox()
            edit.setMinimum(-1000000)
            edit.setMaximum(1000000)
            edit.setDecimals(2)
            edit.setValue(p.balance)
            self.layout.addRow(f"{p.name} balance:", edit)
            self.balance_edits.append(edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

    def accept(self):
        for p, edit in zip(self.people, self.balance_edits):
            p.balance = edit.value()
        super().accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SplitCalculator()
    window.show()
    sys.exit(app.exec())
