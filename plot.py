import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# CONFIGURAÇÕES DO USUÁRIO (EDITE AQUI!)
# =========================

BASE = "postProcessing"
FORCES_DIR = os.path.join(BASE, "forcesHelice") # Confirme se o nome da pasta é forcesHelice mesmo
MONITOR_DIR = os.path.join(BASE, "monitoramento")

# Suas pastas de tempo (confira se batem com o que tem lá)
SEGMENTS = ["0", "1.82", "4.8"]

# --- CORREÇÃO 1: Eixo Y (o correto para sua simulação) ---
TORQUE_AXIS = "y"           

# --- EDITE ESTES VALORES COM OS DADOS DA SUA GEOMETRIA ---
OMEGA = 106              
R = 0.218                
V_WIND = 6.0             

ETA_GEN = 0.85             # Eficiência do gerador (estimativa)
RHO = 1.225                # Densidade do ar

# Ajuste da janela de média (Pega do segundo 2.0 até o fim)
STEADY_T_MIN = 2.0         
STEADY_T_MAX = None        

SAVE_FIGS = True           
FIG_DIR = "figs"           

# =========================
# FUNÇÕES DE LEITURA
# =========================

_float_re = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?")

def read_openfoam_dat(path: str) -> pd.DataFrame:
    rows = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                nums = [float(x) for x in _float_re.findall(s)]
                if len(nums) < 2:
                    continue
                rows.append(nums)
    except Exception as e:
        print(f"Erro ao ler {path}: {e}")
        return pd.DataFrame()

    if not rows:
        return pd.DataFrame()

    max_len = max(len(r) for r in rows)
    padded = [r + [np.nan] * (max_len - len(r)) for r in rows]
    cols = ["time"] + [f"c{i}" for i in range(1, max_len)]
    df = pd.DataFrame(padded, columns=cols)
    return df.dropna(subset=["time"]).reset_index(drop=True)

def load_segmented_dat(root_dir: str, segments: list[str], filename: str) -> pd.DataFrame:
    parts = []
    print(f"Lendo '{filename}' das pastas: {segments}")
    for seg in segments:
        path = os.path.join(root_dir, seg, filename)
        if not os.path.exists(path):
            print(f"AVISO: Arquivo não encontrado: {path}")
            continue
        df = read_openfoam_dat(path)
        if not df.empty:
            df["segment"] = seg
            parts.append(df)
    
    if not parts:
        raise FileNotFoundError(f"Nenhum arquivo {filename} válido encontrado nas pastas indicadas.")

    out = pd.concat(parts, ignore_index=True)
    out = out.sort_values("time", kind="mergesort")
    return out.drop_duplicates(subset=["time"], keep="last").reset_index(drop=True)

# =========================
# EXTRAÇÃO DE TORQUE
# =========================

_axis_to_idx = {"x": 0, "y": 1, "z": 2}

def extract_torque_from_moment(df_moment: pd.DataFrame, axis: str) -> np.ndarray:
    axis = axis.lower()
    idx = _axis_to_idx[axis]
    
    # Filtra apenas colunas de dados numéricos (c1, c2, c3...)
    numeric_cols = [c for c in df_moment.columns if c.startswith("c")]
    
    if len(numeric_cols) < 3:
         raise ValueError("Arquivo de momento corrompido ou formato desconhecido.")

    # Pega apenas as colunas 0, 1 e 2 (Total Forces)
    m_total = df_moment[numeric_cols[0:3]].to_numpy()
    
    return m_total[:, idx]

# =========================
# CÁLCULOS E PLOTS
# =========================

def compute_metrics(time: np.ndarray, torque: np.ndarray) -> dict:
    # Potência Mecânica = Torque * Omega
    # Usamos abs(torque) porque torque negativo só indica direção horária
    p_we = np.abs(torque) * OMEGA 
    p_ele = ETA_GEN * p_we

    a_w = np.pi * R**2
    p_wind = 0.5 * RHO * a_w * V_WIND**3

    e = np.zeros_like(p_ele)
    dt = np.diff(time)
    if len(dt) > 0:
        # Integração com trapezio    para energia acumulada (Joules)
        e[1:] = np.cumsum(0.5 * (p_ele[1:] + p_ele[:-1]) * dt)

    return {"P_we": p_we, "P_ele": p_ele, "E": e, "P_wind": p_wind}

def plot_series(time, y, title, y_label, fig_name, color='blue'):
    plt.figure(figsize=(10, 6))
    plt.plot(time, y, color=color, linewidth=1.5)
    plt.xlabel("Tempo (s)", fontsize=12)
    plt.ylabel(y_label, fontsize=12)
    plt.title(title, fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Zoom automático para evitar linhas coladas no topo/fundo
    if np.std(y) > 0:
        mean_val = np.mean(y)
        std_val = np.std(y)
        plt.ylim(mean_val - 4*std_val, mean_val + 4*std_val)

    if SAVE_FIGS:
        os.makedirs(FIG_DIR, exist_ok=True)
        path = os.path.join(FIG_DIR, fig_name)
        plt.savefig(path, dpi=150, bbox_inches="tight")
        print(f"Salvo: {path}")
    plt.show()

# =========================
# PRINCIPAL
# =========================

def main():
    print("--- Iniciando Processamento ---")
    
    # 1. Carregar dados
    df_moment = load_segmented_dat(FORCES_DIR, SEGMENTS, "moment.dat")
    time = df_moment["time"].to_numpy()
    
    # 2. Extrair Torque (com correção de eixo e soma)
    torque = extract_torque_from_moment(df_moment, TORQUE_AXIS)
    
    # 3. Calcular Métricas
    metrics = compute_metrics(time, torque)
    
    # 4. Médias no Regime Permanente
    # Filtra os dados dentro da janela definida (ex: > 2.0s)
    mask = (time >= STEADY_T_MIN)
    if STEADY_T_MAX:
        mask = mask & (time <= STEADY_T_MAX)
        
    if not np.any(mask):
        print("ERRO: Janela de tempo inválida. Verifique STEADY_T_MIN.")
        return

    torque_mean = np.mean(torque[mask])
    torque_mean_abs = np.abs(torque_mean) # Usamos módulo para apresentar
    p_we_mean = np.mean(metrics["P_we"][mask])
    
    # Cp (Coeficiente de Potência) = Potência Extraída / Potência do Vento
    cp = p_we_mean / metrics["P_wind"] if metrics["P_wind"] != 0 else 0

    print("\n" + "="*30)
    print("      RESULTADOS FINAIS      ")
    print("="*30)
    print(f"Velocidade Vento: {V_WIND} m/s")
    print(f"Rotação (Omega):  {OMEGA} rad/s")
    print(f"Raio da Turbina:  {R} m")
    print("-" * 30)
    print(f"Torque Médio:     {torque_mean_abs:.4f} N.m")
    print(f"Potência Mecânica:{p_we_mean:.4f} Watts")
    print(f"Coeficiente Cp:   {cp:.4f} ({cp*100:.2f}%)")
    print("="*30 + "\n")

    # 5. Gerar Gráficos
    plot_series(time, torque, "Torque Aerodinâmico (Bruto)", "Torque (N.m)", "01_torque.png", color='#1f77b4')
    plot_series(time, metrics["P_we"], "Potência Mecânica Instantânea", "Potência (W)", "02_potencia.png", color='#ff7f0e')
    plot_series(time, metrics["E"], "Energia Acumulada", "Energia (Joules)", "03_energia.png", color='#2ca02c')

if __name__ == "__main__":
    main()