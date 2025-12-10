#!/bin/bash
set -e

# --- CONFIGURAÇÕES RYZEN 5 5600G ---
NP=6
MPI_EXEC="/usr/bin/mpirun"
SOLVER="pimpleFoam"

echo "-----------------------------------"
echo "🚀 INICIANDO NOVA SIMULAÇÃO (Solid Body Motion)"
echo "-----------------------------------"

# 1. LIMPEZA (CRÍTICO PARA MUDANÇA DE FÍSICA)
echo "🧹 Limpando arquivos antigos e processadores..."
# Apaga pastas de tempo (0.1, 0.2...) mas mantém a pasta 0 original
ls -d [1-9]* 0.* processor* | xargs rm -rf 2>/dev/null || true
echo "   -> Pasta limpa."

# 2. DECOMPOSIÇÃO
echo "🔢 Decompondo o domínio para $NP núcleos..."
decomposePar > log.decompose
echo "   -> Decomposição concluída."

# 3. EXECUÇÃO
echo "🔥 Rodando Solver ($SOLVER) em paralelo..."
$MPI_EXEC -np $NP $SOLVER -parallel > log.simulation_solidBody

echo "✅ Fim da execução."
echo "   Acompanhe com: tail -f log.simulation_solidBody"