#!/bin/bash
set -e

# --- CONFIGURAÇÕES ---
NP=6
# VOLTANDO AO QUE FUNCIONAVA + OVERSUBSCRIBE PARA EVITAR ERRO
MPI_EXEC="/usr/bin/mpirun"
MPI_FLAGS="--oversubscribe" 
SOLVER="pimpleFoam"

echo "-----------------------------------"
echo "🚀 INICIANDO NOVA SIMULAÇÃO (Versão Final)"
echo "-----------------------------------"

# 1. LIMPEZA SEGURA
echo "🧹 Limpando arquivos antigos..."
rm -rf processor*
# Limpa tempos numéricos (ex: 0.1, 10) mas preserva 0 e 0.orig
ls -d [1-9]* 2>/dev/null | xargs rm -rf || true

# 1.1 GARANTIR A PASTA 0
# Se a pasta 0 não existir, mas a 0.orig existir, restaura ela.
if [ ! -d "0" ] && [ -d "0.orig" ]; then
    echo "♻️  Restaurando pasta 0 a partir de 0.orig..."
    cp -r 0.orig 0
fi

# 2. DECOMPOSIÇÃO
echo "🔢 Decompondo o domínio para $NP núcleos..."
# O copyZero é essencial. Se falhar, verifique se a pasta 0 existe.
decomposePar -copyZero -force > log.decompose
echo "   -> Decomposição concluída."

# 3. EXECUÇÃO
echo "Rodando Solver ($SOLVER) em paralelo..."

LOG_KEY="log.simulation_solidBody"
LOG_INTERVAL_SEC=5

$MPI_EXEC $MPI_FLAGS -np $NP $SOLVER -parallel 2>&1 \
  | stdbuf -oL -eL awk -v s="$LOG_INTERVAL_SEC" '
      BEGIN { t = systime() }

      # Sempre registra mensagens críticas
      /FOAM FATAL|Floating point|SIGFPE|Segmentation fault|error|Error/ {
        print
        fflush()
        next
      }

      # Linhas que você quer acompanhar, mas limitadas por tempo de relógio
      /^(Time =|Courant Number|ExecutionTime|forces)/ {
        now = systime()
        if (now - t >= s) {
          print
          fflush()
          t = now
        }
      }
    ' > "$LOG_KEY"

echo "Fim da execução."
echo "Acompanhe com: tail -f $LOG_KEY"