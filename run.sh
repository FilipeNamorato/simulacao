#!/bin/bash
set -e

# --- CONFIGURAÇÕES RYZEN 5 5600G ---
NP=6
MPI_EXEC="/usr/bin/mpirun"
SOLVER="pimpleFoam"  # <--- CORRIGIDO: v2412 usa pimpleFoam para tudo

echo "-----------------------------------"
echo "🚀 Iniciando Simulação 6DoF (pimpleFoam)"
echo "-----------------------------------"

echo "🧹 Restaurando condições iniciais..."
if [ -d "0.orig" ]; then
    rm -rf 0
    cp -r 0.orig 0
elif [ -d "zero.org" ]; then
    rm -rf 0
    cp -r zero.org 0
else
    echo "⚠️  Usando pasta 0 existente."
fi

echo "🔢 Decompondo..."
decomposePar -force > log.decomposePar

echo "🔁 Renumerando..."
$MPI_EXEC -np $NP renumberMesh -overwrite -parallel > log.renumberMesh

echo "🔥 Rodando Simulação..."
# Roda o solver
$MPI_EXEC -np $NP $SOLVER -parallel > log.simulation

echo "📦 Reconstruindo..."
reconstructPar > log.reconstructPar

echo "✅ Fim."