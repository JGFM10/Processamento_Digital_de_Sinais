import serial
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore
import sys
import numpy as np
from scipy import signal

# === CONFIGURAÇÕES ===
# Atenção: Certifique-se de que a porta serial esteja disponível e correta
porta_serial = 'COM9'   # Ajuste conforme necessário
baud_rate = 115200
fs = 2000                 # Frequência de amostragem em Hz
num_amostras = 500

# === ABRIR SERIAL ===
try:
    ser = serial.Serial(porta_serial, baud_rate)
    print(f"Porta serial {porta_serial} aberta com sucesso.")
except serial.SerialException as e:
    print(f"Erro ao abrir a porta serial {porta_serial}: {e}")
    print("Certifique-se de que a porta está correta e não está em uso por outro programa.")
    sys.exit(1) # Sai do programa se não conseguir abrir a serial

# === PARÂMETROS INICIAIS DO FILTRO ===
ordem_inicial = 4
cutoff_freq_inicial = 100  # Hz
cutoff_freq_low_inicial = 50 # Hz (para filtro passa-faixa inicial)
# Coeficientes do filtro (b e a) e estado inicial (zi)
b, a = signal.iirfilter(ordem_inicial, cutoff_freq_inicial / (fs / 2), btype='lowpass')
zi = signal.lfilter_zi(b, a) # Estado inicial do filtro

# === INTERFACE GRÁFICA ===
app = QtWidgets.QApplication(sys.argv)
main_win = QtWidgets.QWidget()
main_layout = QtWidgets.QVBoxLayout(main_win)

# === CONTROLES DO FILTRO ===
controls_layout = QtWidgets.QHBoxLayout()

label_tipo_filtro = QtWidgets.QLabel("Tipo:")
combo_tipo_filtro = QtWidgets.QComboBox()
combo_tipo_filtro.addItems(["Passa-Baixa", "Passa-Alta", "Passa-Faixa"])
combo_tipo_filtro.setCurrentText("Passa-Baixa") # Define o padrão

label_ordem = QtWidgets.QLabel("Ordem:")
input_ordem = QtWidgets.QLineEdit(str(ordem_inicial))
input_ordem.setFixedWidth(60)

# Campo para a frequência de corte inferior (visível apenas para passa-faixa)
label_cutoff_low = QtWidgets.QLabel("F. Corte Inf. (Hz):")
input_cutoff_low = QtWidgets.QLineEdit(str(cutoff_freq_low_inicial))
input_cutoff_low.setFixedWidth(60)
input_cutoff_low.setVisible(False) 

# Campo para a frequência de corte (superior em passa-faixa, única em passa-baixa/alta)
label_cutoff = QtWidgets.QLabel("F. Corte (Hz):")
input_cutoff = QtWidgets.QLineEdit(str(cutoff_freq_inicial))
input_cutoff.setFixedWidth(60)

# Nova caixa de seleção para ativar/desativar o filtro
checkbox_sem_filtro = QtWidgets.QCheckBox("Sem Filtro")
checkbox_sem_filtro.setChecked(False) 

btn_aplicar = QtWidgets.QPushButton("Aplicar Filtro")

# Adiciona os widgets ao layout de controle
controls_layout.addWidget(label_tipo_filtro)
controls_layout.addWidget(combo_tipo_filtro)
controls_layout.addWidget(label_ordem)
controls_layout.addWidget(input_ordem)
controls_layout.addWidget(label_cutoff_low)
controls_layout.addWidget(input_cutoff_low)
controls_layout.addWidget(label_cutoff)
controls_layout.addWidget(input_cutoff)
controls_layout.addWidget(checkbox_sem_filtro) # Adiciona o checkbox
controls_layout.addWidget(btn_aplicar)


main_layout.addLayout(controls_layout)

# === GRÁFICOS ===
win = pg.GraphicsLayoutWidget()
main_layout.addWidget(win)

plot_time = win.addPlot(title="Sinal (Tempo)") 
plot_time.setYRange(0, 1024) 
curve_time = plot_time.plot(pen='r')
plot_time.setLabel('left', 'Amplitude')
plot_time.setLabel('bottom', 'Amostras')

win.nextRow()
plot_fft = win.addPlot(title="FFT (Frequência)") 
plot_fft.setYRange(0, 15000) 
plot_fft.setXRange(0, fs / 2) 
curve_fft = plot_fft.plot(pen='b')
plot_fft.setLabel('left', 'Magnitude')
plot_fft.setLabel('bottom', 'Frequência (Hz)')

# Buffer para armazenar os dados e exibir nos gráficos
dados = [0] * num_amostras
dados_brutos = [0] * num_amostras # Buffer para armazenar os dados brutos

# === FUNÇÃO PARA ATUALIZAR O FILTRO ===
def atualizar_filtro():
    global b, a, zi 
    try:
        if checkbox_sem_filtro.isChecked(): # Se "Sem Filtro" estiver marcado, não precisamos recalcular o filtro
            print("Filtro desativado.")
            return

        nova_ordem = int(input_ordem.text())
        if nova_ordem <= 0:
            raise ValueError("A ordem do filtro deve ser um número inteiro positivo.")

        tipo_filtro_selecionado = combo_tipo_filtro.currentText()
        nyquist = fs / 2 

        if tipo_filtro_selecionado == "Passa-Faixa":
            nova_cutoff_low = float(input_cutoff_low.text())
            nova_cutoff_high = float(input_cutoff.text())

            if not (0 < nova_cutoff_low < nyquist and 0 < nova_cutoff_high < nyquist and nova_cutoff_low < nova_cutoff_high):
                raise ValueError("Frequências de corte inválidas para Passa-Faixa. Devem ser > 0, < Nyquist, e Inferior < Superior.")
            
            # Normaliza as frequências de corte para o cálculo do filtro
            b, a = signal.iirfilter(nova_ordem, [nova_cutoff_low / nyquist, nova_cutoff_high / nyquist], btype='bandpass')
        else:
            nova_cutoff = float(input_cutoff.text())
            if not (0 < nova_cutoff < nyquist):
                raise ValueError(f"Frequência de corte inválida para {tipo_filtro_selecionado}. Deve ser > 0 e < Nyquist ({nyquist} Hz).")

            if tipo_filtro_selecionado == "Passa-Baixa":
                b, a = signal.iirfilter(nova_ordem, nova_cutoff / nyquist, btype='lowpass')
            elif tipo_filtro_selecionado == "Passa-Alta":
                b, a = signal.iirfilter(nova_ordem, nova_cutoff / nyquist, btype='highpass')
            else: # Caso padrão para evitar erros (nunca deve acontecer com as opções do combobox)
                raise ValueError("Tipo de filtro desconhecido.")

        # Reinicializa o estado do filtro 
        zi = signal.lfilter_zi(b, a)
        print(f"Filtro {tipo_filtro_selecionado} de ordem {nova_ordem} aplicado.")
    except ValueError as ve:
        QtWidgets.QMessageBox.warning(main_win, "Erro de Parâmetro", str(ve))
        print("Erro de Parâmetro:", ve)
    except Exception as e:
        QtWidgets.QMessageBox.critical(main_win, "Erro Inesperado", f"Ocorreu um erro ao aplicar o filtro: {e}")
        print("Erro inesperado ao aplicar filtro:", e)

# Função para controlar a visibilidade dos campos de frequência de corte
def gerenciar_visibilidade_cortes():
    # Desativa todos os controles de filtro se "Sem Filtro" estiver marcado
    is_sem_filtro = checkbox_sem_filtro.isChecked()
    combo_tipo_filtro.setEnabled(not is_sem_filtro)
    input_ordem.setEnabled(not is_sem_filtro)
    input_cutoff.setEnabled(not is_sem_filtro)
    input_cutoff_low.setEnabled(not is_sem_filtro)
    label_ordem.setEnabled(not is_sem_filtro)
    label_tipo_filtro.setEnabled(not is_sem_filtro)
    label_cutoff.setEnabled(not is_sem_filtro)
    label_cutoff_low.setEnabled(not is_sem_filtro)

    if is_sem_filtro:
        
        label_cutoff_low.setVisible(False)
        input_cutoff_low.setVisible(False)
        label_cutoff.setVisible(False)
        input_cutoff.setVisible(False)
        btn_aplicar.setEnabled(False) 
    else:
        btn_aplicar.setEnabled(True)
        tipo_filtro_selecionado = combo_tipo_filtro.currentText()
        if tipo_filtro_selecionado == "Passa-Faixa":
            label_cutoff.setText("F. Corte Sup. (Hz):")
            label_cutoff_low.setVisible(True)
            input_cutoff_low.setVisible(True)
            label_cutoff.setVisible(True) 
            input_cutoff.setVisible(True)
        else:
            label_cutoff.setText("F. Corte (Hz):")
            label_cutoff_low.setVisible(False)
            input_cutoff_low.setVisible(False)
            label_cutoff.setVisible(True) 
            input_cutoff.setVisible(True)
    
    # Aplica o filtro caso mude a visibilidade
    atualizar_filtro()



btn_aplicar.clicked.connect(atualizar_filtro)
combo_tipo_filtro.currentIndexChanged.connect(gerenciar_visibilidade_cortes)
checkbox_sem_filtro.stateChanged.connect(gerenciar_visibilidade_cortes) 

#Visibilidade Inicial
gerenciar_visibilidade_cortes()

# === FUNÇÃO DE ATUALIZAÇÃO DOS GRÁFICOS ===
def update():
    global dados, dados_brutos, zi
    while ser.in_waiting: 
        try:
            linha = ser.readline().decode().strip() 
            if linha:
                valor_bruto = float(linha) # Valor lido do serial
                
                # Armazena o valor bruto no buffer de dados brutos
                dados_brutos = dados_brutos[1:] + [valor_bruto]

                # Decide qual valor usar (filtrado ou bruto)
                if checkbox_sem_filtro.isChecked():
                    valor_para_exibir = valor_bruto
                    zi = signal.lfilter_zi(b,a) # Reinicializa para evitar acumular estado
                else:
                    # Aplica o filtro digital ao valor atual, mantendo o estado
                    y, zi = signal.lfilter(b, a, [valor_bruto], zi=zi)
                    valor_para_exibir = y[0]
                
                # Adiciona o valor (filtrado ou bruto) ao buffer de dados para o gráfico de tempo
                dados = dados[1:] + [valor_para_exibir]
                
                # Atualiza o gráfico do sinal no tempo
                curve_time.setData(dados)

                # Prepara os dados para a FFT (sempre os dados que estão sendo exibidos no gráfico de tempo)
                dados_fft_calc = np.array(dados)
                
                # Remove a componente DC (média) para melhorar a visualização da FFT
                dados_fft_calc -= np.mean(dados_fft_calc) 
                
                # Calcula a FFT (rfft para sinais reais) e suas frequências correspondentes
                fft_vals = np.abs(np.fft.rfft(dados_fft_calc))
                freqs = np.fft.rfftfreq(len(dados_fft_calc), d=1/fs)
                
                # Atualiza o gráfico da FFT
                curve_fft.setData(freqs, fft_vals)
        except ValueError:
            # Ignora linhas que não podem ser convertidas para float (ex: linhas vazias, lixo)
            pass
        except Exception as e:
            # Captura outras exceções inesperadas durante a leitura/processamento
            print(f"Erro na atualização: {e}")
            pass # Continua tentando ler a serial

# === TIMER ===
# O timer chama a função update() periodicamente para manter os gráficos atualizados
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(1) # Chama a cada 1 ms (o mais rápido possível)

# === EXECUTAR INTERFACE ===
main_win.setWindowTitle("Análise de Sinal em Tempo Real com Filtragem Dinâmica")
main_win.show()

# Garante que a porta serial seja fechada ao sair
def close_serial_on_exit():
    if ser.is_open:
        ser.close()
        print("Porta serial fechada.")

app.aboutToQuit.connect(close_serial_on_exit)
sys.exit(app.exec_())