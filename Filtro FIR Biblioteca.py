import serial
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore
import sys
import numpy as np
from scipy.signal import remez, lfilter

# === CONFIGURAÇÕES INICIAIS ===
porta_serial = 'COM14'
baud_rate = 115200
num_amostras = 500

# === VARIÁVEIS GLOBAIS ===
fir_coef = np.array([1.0])  # coeficientes iniciais (sem filtro)
zi = np.zeros(1)
fs = 2000

# === ABRIR SERIAL ===
ser = serial.Serial(porta_serial, baud_rate)

# === INTERFACE ===
app = QtWidgets.QApplication(sys.argv)
main_win = QtWidgets.QWidget()
main_layout = QtWidgets.QVBoxLayout(main_win)

# === CONTROLES DE FILTRO ===
controls_layout = QtWidgets.QHBoxLayout()

def add_input(label_text, default, width=60):
    label = QtWidgets.QLabel(label_text)
    box = QtWidgets.QLineEdit(str(default))
    box.setFixedWidth(width)
    controls_layout.addWidget(label)
    controls_layout.addWidget(box)
    return box

input_fs = add_input("fs (Hz):", 2000)
input_wp = add_input("Ωp (Hz):", 850)
input_wr = add_input("Ωr (Hz):", 900)
input_k = add_input("Ganho:", 1.0)
input_m = add_input("Ordem M:", 51)

btn_atualizar = QtWidgets.QPushButton("Atualizar Filtro")
controls_layout.addWidget(btn_atualizar)

main_layout.addLayout(controls_layout)

# === GRÁFICOS ===
win = pg.GraphicsLayoutWidget()
main_layout.addWidget(win)

plot_time = win.addPlot(title="Sinal filtrado")
plot_time.setYRange(-1024, 1024)
curve_time = plot_time.plot(pen='r')

win.nextRow()
plot_fft = win.addPlot(title="FFT (Transformada Rápida de Fourier)")
plot_fft.setYRange(0, 15000)
curve_fft = plot_fft.plot(pen='b')

dados = [0.0] * num_amostras

# === FUNÇÃO PARA ATUALIZAR O FILTRO ===
def atualizar_filtro():
    global fir_coef, zi, fs

    try:
        fs = float(input_fs.text())
        wp = float(input_wp.text())
        wr = float(input_wr.text())
        k = float(input_k.text())
        m = int(input_m.text())

        # Normalize as frequências (para remez elas vão de 0 a fs/2 → faixa [0, 0.5])
        nyq = fs / 2
        bands = [0, wp, wr, nyq]
        desired = [k, 0]
        fir_coef = remez(m, bands, desired, fs=fs)
        zi = np.zeros(len(fir_coef) - 1)
        print("Filtro atualizado.")
    except Exception as e:
        print("Erro ao atualizar filtro:", e)

# Conecta botão
btn_atualizar.clicked.connect(atualizar_filtro)

# Inicializa filtro com valores padrão
atualizar_filtro()

# === FUNÇÃO DE ATUALIZAÇÃO ===
def update():
    global dados, zi

    while ser.in_waiting:
        try:
            linha = ser.readline().decode().strip()
            if not linha:
                continue
            x = float(linha)

            # Aplica filtro FIR
            y, zi = lfilter(fir_coef, 1.0, [x], zi=zi)
            y = y[0]

            dados = dados[1:] + [y]
            curve_time.setData(dados)

            dados_fft = np.array(dados)
            dados_fft -= np.mean(dados_fft)
            fft_vals = np.abs(np.fft.rfft(dados_fft))
            freqs = np.fft.rfftfreq(len(dados_fft), d=1/fs)
            curve_fft.setData(freqs, fft_vals)
        except:
            pass

# === TIMER DE ATUALIZAÇÃO ===
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(1)

# === EXECUTAR INTERFACE ===
main_win.setWindowTitle("Filtro FIR com Parâmetros Personalizáveis")
main_win.show()
sys.exit(app.exec_())
