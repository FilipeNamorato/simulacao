import matplotlib.pyplot as plt
import numpy as np
import sys

# --- CONFIGURAÇÃO ---
arquivo_dados = 'historico_torque.dat' # O arquivo que você juntou com 'cat'
coluna_tempo = 0
coluna_torque_y = 2  # Baseado no cabeçalho: Time(0) total_x(1) total_y(2)

print(f"--- Lendo arquivo: {arquivo_dados} ---")

times = []
torques = []

try:
    with open(arquivo_dados, 'r') as f:
        for line_num, line in enumerate(f):
            # Limpeza automática:
            # Pula linhas de comentário (#) ou linhas vazias
            if line.strip().startswith('#') or not line.strip():
                continue
            
            try:
                parts = line.split()
                # Tenta converter para número. Se falhar (ex: cabeçalho repetido), o código ignora a linha.
                t = float(parts[coluna_tempo])
                ty = float(parts[coluna_torque_y])
                
                times.append(t)
                torques.append(ty)
            except (ValueError, IndexError):
                 # Se der erro na conversão, é lixo no arquivo, apenas ignora
                continue

except FileNotFoundError:
    print(f"ERRO: O arquivo '{arquivo_dados}' não foi encontrado.")
    print("Você rodou o comando 'cat ... > historico_torque.dat'?")
    sys.exit(1)

if not times:
    print("ERRO: Nenhum dado válido foi lido. Verifique o arquivo.")
    sys.exit(1)

print(f"Sucesso! Lidos {len(times)} pontos de dados até o tempo {times[-1]:.2f}s.")
print("Gerando gráfico...")

# --- PLOTAGEM ---
plt.figure(figsize=(12, 7)) # Tamanho bom para relatório

# Plota os dados com uma linha azul ligeiramente transparente
plt.plot(times, torques, label='Torque Y (Mz)', color='#1f77b4', linewidth=1.5, alpha=0.9)

# --- O SEGREDO DO GRÁFICO BONITO (ZOOM AUTOMÁTICO) ---
# Calcula a média e o desvio padrão para focar onde importa
avg_torque = np.mean(torques)
std_torque = np.std(torques)

# Se o desvio for muito pequeno (simulação muito estável), força uma pequena margem
if std_torque < abs(avg_torque) * 0.01:
    margin = abs(avg_torque) * 0.05 # 5% de margem
else:
    margin = std_torque * 3 # 3 sigmas de margem

plt.ylim(avg_torque - margin, avg_torque + margin)
# ------------------------------------------------------

# Perfumaria para ficar profissional
plt.grid(True, which='major', linestyle='-', linewidth=0.75, color='gray', alpha=0.3)
plt.grid(True, which='minor', linestyle=':', linewidth=0.5, color='gray', alpha=0.2)
plt.minorticks_on()

plt.xlabel('Tempo de Simulação (s)', fontsize=12, fontweight='bold')
plt.ylabel('Torque Aerodinâmico (N.m)', fontsize=12, fontweight='bold')
plt.title('Histórico de Convergência do Torque', fontsize=14, pad=15)
plt.legend(fontsize=11)

# Adiciona uma anotação com o valor médio final
plt.annotate(f'Média Final: {torques[-1]:.4f} N.m', 
             xy=(times[-1], torques[-1]), 
             xytext=(times[-1]*0.7, torques[-1] + margin*0.2),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1.5),
             fontsize=10, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", lw=1))

plt.tight_layout()

# Salva a imagem em alta resolução
nome_imagem = 'Resultado_Torque_Final.png'
plt.savefig(nome_imagem, dpi=300, bbox_inches='tight')
print(f"✅ Gráfico salvo como '{nome_imagem}' e exibido na tela.")
print("Pode respirar aliviado!")
plt.show()