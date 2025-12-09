#!/bin/bash
set -e

# --- CONFIGURAÇÕES RYZEN 5 5600G ---
NP=6
MPI_EXEC="/usr/bin/mpirun"
SOLVER="pimpleFoam"

echo "-----------------------------------"
echo "🔄 RETOMANDO Simulação 6DoF"
echo "-----------------------------------"

# --- BLOCO DE DESTRUIÇÃO DESATIVADO ---
# (Não queremos limpar a pasta 0 nem decompor de novo)
# echo "🧹 Restaurando condições iniciais..."
# rm -rf 0 ...
# echo "🔢 Decompondo..."
# decomposePar ...
# echo "🔁 Renumerando..."
# renumberMesh ...
# --------------------------------------

echo "⚠️  Checagem rápida:"
echo "   1. As pastas 'processor0' a 'processor5' estão aí?"
echo "   2. O controlDict está com 'startFrom latestTime;' ?"
echo "-----------------------------------"

echo "🔥 Rodando Simulação (Continuando)..."

# Roda o solver em paralelo. 
# Ele vai procurar automaticamente o último tempo dentro das pastas processor*
# Estou salvando num log novo para você não perder o histórico do erro antigo
$MPI_EXEC -np $NP $SOLVER -parallel > log.simulation_continue

echo "✅ Fim da execução."
echo "   Verifique o arquivo 'log.simulation_continue' para acompanhar."