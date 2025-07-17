import serial
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore
import sys
import numpy as np

# === CONFIGURAÇÕES ===
porta_serial = 'COM14'     # Ajuste conforme necessário
baud_rate = 115200
fs = 2000                 # Frequência de amostragem em Hz
num_amostras = 500

# === ABRIR SERIAL ===
ser = serial.Serial(porta_serial, baud_rate)

# === SETUP DA INTERFACE PRINCIPAL ===
app = QtWidgets.QApplication(sys.argv)
main_win = QtWidgets.QWidget()
main_layout = QtWidgets.QVBoxLayout(main_win)

# === WIDGETS DE CONTROLE ===
controls_layout = QtWidgets.QHBoxLayout()

label_a = QtWidgets.QLabel("Coef a:")
coef_a_input = QtWidgets.QLineEdit("0.2")
coef_a_input.setFixedWidth(60)

label_b = QtWidgets.QLabel("Coef b:")
coef_b_input = QtWidgets.QLineEdit("0.4")
coef_b_input.setFixedWidth(60)

controls_layout.addWidget(label_a)
controls_layout.addWidget(coef_a_input)
controls_layout.addWidget(label_b)
controls_layout.addWidget(coef_b_input)

main_layout.addLayout(controls_layout)

# === GRÁFICOS ===
win = pg.GraphicsLayoutWidget()
main_layout.addWidget(win)

plot_time = win.addPlot(title="porta serial")
plot_time.setYRange(-1024, 1024)
curve_time = plot_time.plot(pen='r')
plot_time.setLabel('left', 'Amplitude')
plot_time.setLabel('bottom', 'Amostras')

win.nextRow()
plot_fft = win.addPlot(title="FFT (Transformada Rápida de Fourier)")
plot_fft.setYRange(0, 15000)
curve_fft = plot_fft.plot(pen='b')
plot_fft.setLabel('left', 'Magnitude')
plot_fft.setLabel('bottom', 'Frequência (Hz)')

dados = [0] * num_amostras

# === FUNÇÃO DE ATUALIZAÇÃO ===
def update():
    global dados
    valor2 = 0
    try:
        a = float(coef_a_input.text())
        b = float(coef_b_input.text())
    except ValueError:
        return  # Ignora se valores inválidos forem inseridos

    while ser.in_waiting:
        try:
            linha = ser.readline().decode().strip()
            if linha:
                valor = float(linha)
                y = a * valor - b * valor2
                valor2 = y
                dados = dados[1:] + [y]
                curve_time.setData(dados)

                dados_fft = np.array(dados)
                dados_fft -= np.mean(dados_fft)
                fft_vals = np.abs(np.fft.rfft(dados_fft))
                freqs = np.fft.rfftfreq(len(dados_fft), d=1/fs)
                curve_fft.setData(freqs, fft_vals)
        except:
            pass

# === TIMER ===
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(1)

# === EXECUTAR INTERFACE ===
main_win.setWindowTitle("Plot Serial com Controle de Coeficientes")
main_win.show()
sys.exit(app.exec_())
