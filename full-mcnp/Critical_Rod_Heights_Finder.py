import os
import re
import subprocess
import time
import matplotlib.pyplot as plt

# =============================================================================
# --- PATH CONFIGURATIONS ---
# =============================================================================
MCNP_ENV_BAT = r"C:\MCNP630\MCNP\mcnp_630_env.bat"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
# --- TIMING & EXECUTION HELPERS ---
# =============================================================================
def format_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{int(h)}h {int(m)}m {s:.1f}s"
    elif m > 0:
        return f"{int(m)}m {s:.1f}s"
    return f"{s:.2f}s"

def updateRodHeight(inputFilename, newHeight):
    inputPath = os.path.join(SCRIPT_DIR, inputFilename)
    with open(inputPath, 'r') as file:
        fileLines = file.readlines()
        
    with open(inputPath, 'w') as file:
        for line in fileLines:
            if re.match(r"^15\s+pz", line):
                file.write(f"15 pz {newHeight:.4f}\n")
            elif re.match(r"^16\s+pz", line):
                file.write(f"16 pz {newHeight - 0.0405:.4f}\n")
            else:
                file.write(line)

def runMcnpSim(inputFilename, runIndex):
    outFile = f"Aura{runIndex}.out"
    tapeFile = f"AuraRuntape{runIndex}"
    sourceFile = f"AuraS{runIndex}"
    
    # Clean up old iterations to prevent append errors
    for tempFile in [outFile, tapeFile, sourceFile]:
        tempPath = os.path.join(SCRIPT_DIR, tempFile)
        if os.path.exists(tempPath):
            try:
                os.remove(tempPath)
            except OSError as e:
                print(f"   [Warning] Could not delete {tempFile}: {e}")
                
    mcnp_command = f"mcnp6 i={inputFilename} o={outFile} r={tapeFile} s={sourceFile} tasks 10"
    
    # Initialize MCNP environment vars, change directory, and run in one shell call
    full_cmd = f'call "{MCNP_ENV_BAT}" && cd /d "{SCRIPT_DIR}" && {mcnp_command}'
    
    print(f"   [Executing] {mcnp_command}")
    start_time = time.time()
    subprocess.run(full_cmd, shell=True)
    time.sleep(3)
    print(f"   [Done in {format_time(time.time() - start_time)}]")
    
    outPath = os.path.join(SCRIPT_DIR, outFile)
    if not os.path.exists(outPath):
        print(f"   [FATAL ERROR] MCNP failed to generate {outFile}.")
        
    return outPath

def parseKeff(outputFilename):
    if not os.path.exists(outputFilename):
        return None, None
        
    with open(outputFilename, 'r') as file:
        outputData = file.read()
        
    keffMatch = re.search(r"\|\s*the final estimated combined collision/absorption/track-length keff =\s+([\d\.]+)\s+with an estimated standard deviation of\s+([\d\.]+)\s*\|", outputData)
    
    if keffMatch:
        return float(keffMatch.group(1)), float(keffMatch.group(2))
    return None, None

def plotCriticalityApproach(rodHeights, keffValues, stdDeviations):
    plt.figure(figsize=(10, 6))
    plt.errorbar(rodHeights, keffValues, yerr=stdDeviations, fmt='-o', capsize=5, label='k_eff ± std', color='black')
    plt.axhline(y=1.0, color='red', linestyle='--', label='Critical (k_eff = 1.0)')
    
    plt.xlabel('Control Rod Height (cm)')
    plt.ylabel('Effective Multiplication Factor (k_eff)')
    plt.title('Approach to Criticality: Secant Method Iteration')
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.tight_layout()
    plt.show()

# =============================================================================
# --- MAIN SECANT ORCHESTRATOR ---
# =============================================================================
def findCriticalHeight():
    inputFilename = "Aura_MCNP_Model.inp"
    targetKeff = 1.0
    tolerance = 0.00010 
    
    height0 = 150.0
    height1 = 200.0
    
    recordedHeights = []
    recordedKeffs = []
    recordedStds = []

    print(f"\n========== STARTING SECANT ITERATION ==========")
    print(f"Iteration 0: Testing initial guess {height0} cm")
    updateRodHeight(inputFilename, height0)
    outFile0 = runMcnpSim(inputFilename, "0")
    k0, std0 = parseKeff(outFile0)
    
    if k0 is None:
        print("   [HALTING] MCNP execution failure on Iteration 0.")
        return
        
    recordedHeights.append(height0)
    recordedKeffs.append(k0)
    recordedStds.append(std0)
    print(f"   >> Result 0: k_eff = {k0} ± {std0}")

    print(f"\nIteration 1: Testing initial guess {height1} cm")
    updateRodHeight(inputFilename, height1)
    outFile1 = runMcnpSim(inputFilename, "1")
    k1, std1 = parseKeff(outFile1)
    
    if k1 is None:
        print("   [HALTING] MCNP execution failure on Iteration 1.")
        return
        
    recordedHeights.append(height1)
    recordedKeffs.append(k1)
    recordedStds.append(std1)
    print(f"   >> Result 1: k_eff = {k1} ± {std1}")

    runIndex = 2
    pipeline_start_time = time.time()
    
    while abs(k1 - targetKeff) > tolerance:
        if k1 == k0:
            print("\n   [ERROR] k_eff did not change between iterations. Control rod worth may be zero in this region.")
            break
            
        nextHeight = height1 - (k1 - targetKeff) * (height1 - height0) / (k1 - k0)
        print(f"\nIteration {runIndex}: Next estimated height = {nextHeight:.4f} cm")
        
        updateRodHeight(inputFilename, nextHeight)
        nextOutFile = runMcnpSim(inputFilename, str(runIndex))
        kNext, stdNext = parseKeff(nextOutFile)
        
        if kNext is None:
            print("   [HALTING] MCNP execution failed during iteration.")
            break
            
        recordedHeights.append(nextHeight)
        recordedKeffs.append(kNext)
        recordedStds.append(stdNext)
        print(f"   >> Result {runIndex}: k_eff = {kNext} ± {stdNext}")
        
        height0 = height1
        k0 = k1
        height1 = nextHeight
        k1 = kNext
        runIndex += 1

    total_elapsed = time.time() - pipeline_start_time
    print("\n" + "="*70)
    print(f" CRITICALITY SEARCH COMPLETE!")
    print(f" Estimated Critical Control Rod Height: {height1:.4f} cm")
    print(f" Final k_eff: {k1} ± {std1}")
    print(f" Total Iteration Time: {format_time(total_elapsed)}")
    print("="*70)
    
    plotCriticalityApproach(recordedHeights, recordedKeffs, recordedStds)

if __name__ == "__main__":
    findCriticalHeight()