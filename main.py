import sys
import subprocess
import psutil
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QFileDialog,
    QLabel,
    QListWidget,
    QHBoxLayout,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer

class GameOptimizer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("محسن أداء الألعاب")
        self.setGeometry(100, 100, 600, 400)

        self.layout = QVBoxLayout()

        # اختيار اللعبة
        self.select_button = QPushButton("تحديد اللعبة")
        self.select_button.clicked.connect(self.select_game)
        self.layout.addWidget(self.select_button)

        self.game_label = QLabel("لم يتم تحديد لعبة.")
        self.layout.addWidget(self.game_label)

        # تشغيل اللعبة
        self.run_button = QPushButton("تشغيل اللعبة")
        self.run_button.clicked.connect(self.run_game)
        self.run_button.setEnabled(False)
        self.layout.addWidget(self.run_button)

        # قائمة العمليات
        self.process_list = QListWidget()
        self.layout.addWidget(QLabel("العمليات الحالية:"))
        self.layout.addWidget(self.process_list)

        # أزرار إدارة العمليات
        self.process_buttons_layout = QHBoxLayout()
        self.kill_button = QPushButton("إنهاء العملية المحددة")
        self.kill_button.clicked.connect(self.kill_process)
        self.process_buttons_layout.addWidget(self.kill_button)

        self.layout.addLayout(self.process_buttons_layout)

        # مؤشرات الموارد
        self.resource_label = QLabel("حالة الموارد:")
        self.layout.addWidget(self.resource_label)

        # تحديث قائمة العمليات والموارد كل ثانية
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_process_list)
        self.timer.timeout.connect(self.update_resources)
        self.timer.start(1000)

        self.selected_game = None
        self.game_process = None

        self.setLayout(self.layout)

    def select_game(self):
        try:
            # لا نحتاج إلى استخدام Options هنا
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "اختر ملف اللعبة التنفيذي",
                "",
                "Executable Files (*.exe);;All Files (*)",
            )
            if file_name:
                self.selected_game = file_name
                self.game_label.setText(f"العبة المحددة: {file_name}")
                self.run_button.setEnabled(True)
            else:
                self.game_label.setText("لم يتم اختيار أي لعبة.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ في اختيار اللعبة: {e}")

    def run_game(self):
        if self.selected_game:
            try:
                # تشغيل اللعبة
                self.game_process = subprocess.Popen([self.selected_game])

                # تعيين أولوية عالية
                pid = self.game_process.pid
                proc = psutil.Process(pid)
                if sys.platform.startswith('win'):
                    proc.nice(psutil.HIGH_PRIORITY_CLASS)
                else:
                    proc.nice(-10)

                self.game_label.setText(f"تشغيل اللعبة: {self.selected_game} (PID: {pid})")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ في تشغيل اللعبة: {e}")

    def update_process_list(self):
        self.process_list.clear()
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                self.process_list.addItem(f"{proc.info['pid']} - {proc.info['name']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    def kill_process(self):
        selected_item = self.process_list.currentItem()
        if selected_item:
            pid = int(selected_item.text().split(' - ')[0])
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait(timeout=3)
                QMessageBox.information(self, "نجاح", f"تم إنهاء العملية PID: {pid}")
            except psutil.NoSuchProcess:
                QMessageBox.warning(self, "تحذير", "العملية غير موجودة.")
            except psutil.AccessDenied:
                QMessageBox.warning(self, "تحذير", "لا تملك صلاحيات كافية لإنهاء هذه العملية.")
            except psutil.TimeoutExpired:
                proc.kill()
           
              QMessageBox.information(self, "نجاح", f"تم قتل العملية PID: {pid}")
    
    def update_resources(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        net = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
        self.resource_label.setText(f"CPU: {cpu}% | RAM: {ram}% | Network Usage: {net} bytes")

    def closeEvent(self, event):
        # عند إغلاق البرنامج، تأكد من إنهاء اللعبة إذا كانت لا تزال تعمل
        if self.game_process and self.game_process.poll() is None:
            try:
                self.game_process.terminate()
            except:
                pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    optimizer = GameOptimizer()
    optimizer.show()
    sys.exit(app.exec())
