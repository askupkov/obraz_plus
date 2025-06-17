import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                            QTableWidget, QTableWidgetItem, QPushButton, 
                            QMessageBox, QInputDialog, QLineEdit, QLabel, 
                            QComboBox, QFormLayout, QDialog, QTabWidget, QHBoxLayout, QLabel, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QIcon, QFont, QPixmap
import psycopg2


class StyledMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.primary_bg = "#FFFFFF"
        self.secondary_bg = "#BFD6F6"
        self.accent_color = "#405C73"
        self.text_color = "#333332"
        self.setWindowTitle("Система управления производством")
        self.setWindowIcon(QIcon('Образ плюс.ico'))
        self.resize(1000, 700)
        self.setup_styles()

    def setup_styles(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.primary_bg};
            }}
            QTabWidget::pane {{
                border: 1px solid {self.accent_color};
                background: {self.secondary_bg};
                border-radius: 4px;
                margin: 2px;
            }}
            QTabBar::tab {{
                background: {self.secondary_bg};
                color: {self.text_color};
                padding: 8px;
                border: 1px solid {self.accent_color};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background: {self.primary_bg};
                color: {self.accent_color};
                font-weight: bold;
            }}
            QPushButton {{
                background-color: {self.accent_color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #506C8B;
            }}
            QTableWidget {{
                background-color: {self.primary_bg};
                gridline-color: {self.secondary_bg};
                border: 1px solid {self.secondary_bg};
                selection-background-color: {self.accent_color};
                selection-color: white;
            }}
            QHeaderView::section {{
                background-color: {self.accent_color};
                color: white;
                padding: 4px;
                border: none;
            }}
            QLineEdit, QComboBox {{
                border: 1px solid {self.accent_color};
                border-radius: 3px;
                padding: 4px;
            }}
            QLabel {{
                color: {self.text_color};
            }}
        """)


class DatabaseManager:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname="obraz_plus",
            user="postgres",
            password="toor",
            host="localhost",
            port=5432,
            client_encoding='utf-8'
        )
        self.cur = self.conn.cursor()

    def get_materials(self):
        try:
            self.cur.execute("""
                SELECT m.id, m.name, mt.name, 
                       m.unit_price, m.quantity_in_stock, m.min_quantity, 
                       m.quantity_per_package, m.unit
                FROM material m
                JOIN material_type mt ON m.type_id = mt.id
            """)
            return self.cur.fetchall()
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(None, "Ошибка БД", f"Не удалось загрузить материалы: {str(e)}")
            return []

    def add_material(self, name, type_id, price, quantity, min_qty, package_qty, unit):
        try:
            self.cur.execute("""
                INSERT INTO material (
                    name, type_id, unit_price, quantity_in_stock, min_quantity, quantity_per_package, unit
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, type_id, price, quantity, min_qty, package_qty, unit))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def update_material(self, mid, name, type_id, price, quantity, min_qty, package_qty, unit):
        try:
            self.cur.execute("""
                UPDATE material SET name=%s, type_id=%s, unit_price=%s,
                                   quantity_in_stock=%s, min_quantity=%s,
                                   quantity_per_package=%s, unit=%s
                WHERE id=%s
            """, (name, type_id, price, quantity, min_qty, package_qty, unit, mid))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_material(self, mid):
        try:
            self.cur.execute("DELETE FROM material WHERE id=%s", (mid,))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_material_types(self):
        try:
            self.cur.execute("SELECT id, name FROM material_type")
            return self.cur.fetchall()
        except Exception as e:
            self.conn.rollback()
            return []

    def get_products_by_material(self, mid):
        try:
            self.cur.execute("""
                SELECT p.name, pm.required_quantity 
                FROM product_material pm
                JOIN product p ON pm.product_id = p.id
                WHERE pm.material_id = %s
            """, (mid,))
            return self.cur.fetchall()
        except Exception as e:
            self.conn.rollback()
            return []

class MaterialDialog(QDialog):
    def __init__(self, db, material=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить материал" if not material else "Редактировать материал")
        self.db = db
        self.material = material
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()
        self.name_input = QLineEdit()
        self.price_input = QLineEdit()
        self.price_input.setValidator(QDoubleValidator(0, 999999.99, 2))
        self.qty_input = QLineEdit()
        self.qty_input.setValidator(QDoubleValidator(0, 999999.99, 2))
        self.min_qty_input = QLineEdit()
        self.min_qty_input.setValidator(QDoubleValidator(0, 999999.99, 2))
        self.pkg_qty_input = QLineEdit()
        self.pkg_qty_input.setValidator(QDoubleValidator(0, 999999.99, 2))
        self.unit_input = QLineEdit()
        self.type_combo = QComboBox()
        
        types = self.db.get_material_types()
        for tid, tname in types:
            self.type_combo.addItem(tname, tid)

        if self.material:
            self.name_input.setText(self.material[1])
            idx = self.type_combo.findData(self.material[2])
            self.type_combo.setCurrentIndex(idx)
            self.price_input.setText(str(self.material[3]))
            self.qty_input.setText(str(self.material[4]))
            self.min_qty_input.setText(str(self.material[5]))
            self.pkg_qty_input.setText(str(self.material[6]))
            self.unit_input.setText(self.material[7])

        layout.addRow("Наименование:", self.name_input)
        layout.addRow("Тип материала:", self.type_combo)
        layout.addRow("Цена единицы:", self.price_input)
        layout.addRow("Количество на складе:", self.qty_input)
        layout.addRow("Минимальное количество:", self.min_qty_input)
        layout.addRow("Количество в упаковке:", self.pkg_qty_input)
        layout.addRow("Единица измерения:", self.unit_input)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_material)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)

    def save_material(self):
        try:
            name = self.name_input.text()
            type_id = self.type_combo.currentData()
            price = float(self.price_input.text())
            quantity = float(self.qty_input.text())
            min_quantity = float(self.min_qty_input.text())
            package_quantity = float(self.pkg_qty_input.text())
            unit = self.unit_input.text()

            if not name or not unit:
                raise ValueError("Не все обязательные поля заполнены")

            if self.material:
                self.db.update_material(
                    self.material[0], name, type_id, price, quantity,
                    min_quantity, package_quantity, unit
                )
            else:
                self.db.add_material(
                    name, type_id, price, quantity,
                    min_quantity, package_quantity, unit
                )

            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить материал: {str(e)}")


class MainWindow(StyledMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Склад материалов — ООО «Образ плюс»")
        self.db = DatabaseManager()
        self.init_ui()
        self.resize(900, 600)

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Добавление логотипа
        self.logo_label = QLabel(self)
        pixmap = QPixmap("Образ плюс.png")  # Укажите путь к вашему логотипу
        if not pixmap.isNull():
            self.logo_label.setPixmap(pixmap.scaledToWidth(120))  # Сохраняет пропорции, ширина 120px
        else:
            self.logo_label.setText("Логотип не найден")
        self.logo_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.logo_label)

        header = QLabel("Склад материалов — ООО «Образ плюс»")
        header.setStyleSheet(f"""
            QLabel {{
                color: {self.accent_color};
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
            }}
        """)
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Таблица материалов
        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(8)
        self.materials_table.setHorizontalHeaderLabels([
            "ID", "Наименование", "Тип", "Цена", "Остаток", "Минимум", "Упаковка", "Ед."
        ])
        self.materials_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.materials_table.verticalHeader().setVisible(False)
        # Растяжение всех столбцов на всю ширину таблицы
        header = self.materials_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        main_layout.addWidget(self.materials_table)

        # Кнопки
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Добавить")
        edit_btn = QPushButton("✏️ Редактировать")
        del_btn = QPushButton("❌ Удалить")
        use_btn = QPushButton("🔍 Используется в")

        add_btn.clicked.connect(self.add_material)
        edit_btn.clicked.connect(self.edit_material)
        del_btn.clicked.connect(self.delete_material)
        use_btn.clicked.connect(self.show_used_products)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(use_btn)
        main_layout.addLayout(btn_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.load_materials()

    def load_materials(self):
        materials = self.db.get_materials()
        self.materials_table.setRowCount(len(materials))
        for row, material in enumerate(materials):
            for col, value in enumerate(material):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.materials_table.setItem(row, col, item)
        self.materials_table.resizeColumnsToContents()

    def add_material(self):
        dialog = MaterialDialog(self.db)
        if dialog.exec_():
            self.load_materials()

    def edit_material(self):
        selected = self.materials_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите материал для редактирования")
            return
        mid = int(selected[0].text())
        materials = self.db.get_materials()
        material = next((m for m in materials if m[0] == mid), None)
        if material:
            dialog = MaterialDialog(self.db, material)
            if dialog.exec_():
                self.load_materials()

    def delete_material(self):
        selected = self.materials_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите материал для удаления")
            return
        mid = int(selected[0].text())
        reply = QMessageBox.question(self, "Подтверждение", "Вы уверены?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_material(mid)
            self.load_materials()

    def show_used_products(self):
        selected = self.materials_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите материал")
            return
        mid = int(selected[0].text())
        products = self.db.get_products_by_material(mid)

        dialog = QDialog(self)
        dialog.setWindowTitle("Продукция, использующая материал")
        dialog.resize(500, 300)

        layout = QVBoxLayout()
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Продукция", "Необходимое количество"])
        table.setRowCount(len(products))

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Растяжение первого столбца
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Второй по содержимому

        total_required = 0
        for i, (name, qty) in enumerate(products):
            table.setItem(i, 0, QTableWidgetItem(name))
            table.setItem(i, 1, QTableWidgetItem(f"{qty:.2f}"))
            total_required += qty

        summary_label = QLabel(f"Общее необходимое количество: {total_required:.2f}")
        summary_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(table)
        layout.addWidget(summary_label)
        dialog.setLayout(layout)
        dialog.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Constantia", 10)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())