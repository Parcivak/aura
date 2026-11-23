#!/bin/bash
#SBATCH --job-name=aura_sfr_steady
#SBATCH --account=general
#SBATCH --partition=requeue
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=moose_run_%j.out
#SBATCH --error=moose_run_%j.err

# Move to the directory where sbatch was executed
cd "$SLURM_SUBMIT_DIR"

# Load conda and activate the shared MOOSE environment
module load miniconda/miniconda3
source /share/apps/common/miniconda/miniconda3/bin/activate
conda activate /share/apps/common/moose/.moose_conda

# Avoid OpenMP thread oversubscription when running MPI
export OMP_NUM_THREADS=1

# Run MOOSE in parallel with residual & line-search diagnostics
mpiexec -n "$SLURM_NTASKS" combined-opt -i diffusion.i \
  -snes_linesearch_monitor
