#!/usr/bin/env bash
set -euo pipefail

NP=6
MPI_EXEC="/usr/bin/mpirun"
MPI_FLAGS="--oversubscribe"
SOLVER="pimpleFoam"

LOG_KEY="log.simulation_solidBody"
LOG_INTERVAL_SEC=5

echo "Iniciando simulacao"

echo "Limpando caso"
rm -rf processor* postProcessing
rm -f log.* *.log core core.* *.foam

# Remove pastas de tempo numericas, incluindo 0.x, preservando 0 e 0.orig
find . -maxdepth 1 -type d -regextype posix-extended \
  -regex './[0-9]+([.][0-9]+)?' \
  ! -name '0' ! -name '0.orig' -print0 | xargs -0r rm -rf

if [ ! -d "0" ] && [ -d "0.orig" ]; then
  echo "Restaurando pasta 0 a partir de 0.orig"
  cp -r 0.orig 0
fi

echo "Decompondo para $NP processos"
decomposePar -copyZero -force > log.decompose 2>&1

echo "Rodando $SOLVER em paralelo"
$MPI_EXEC $MPI_FLAGS -np "$NP" $SOLVER -parallel 2>&1 \
  | stdbuf -oL -eL awk -v s="$LOG_INTERVAL_SEC" '
      BEGIN { t = systime() }
      /FOAM FATAL|Floating point|SIGFPE|Segmentation fault|error|Error/ { print; fflush(); next }
      /^(Time =|Courant Number|ExecutionTime)/ {
        now = systime()
        if (now - t >= s) { print; fflush(); t = now }
      }
    ' > "$LOG_KEY"

echo "Fim. Acompanhe com: tail -f $LOG_KEY"
