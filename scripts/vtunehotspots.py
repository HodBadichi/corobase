import subprocess
import os
import datetime
import re


def ParseOutput(sOutput, sWantedFunctionName):
    sOutput = sOutput.split("\n")
    for sLine in sOutput:
        if sWantedFunctionName in sLine:
            # Extract the time value from the line using regex
            match = re.search(r'(\d+\.\d+)s', sLine)  # Match a floating point number followed by 's'
            if match:
                time_value = match.group(1)  # Get the matched time value
                return time_value
    raise Exception(f"Function {sWantedFunctionName} not found in output")

def getErmiaCommand(nBatchSize):
    return f"/specific/disk1/hodbadihi/MLP/corobase/build/ermia_SI -physical_workers_only=1 -index_probe_only=1 -node_memory_gb=80 -null_log_device=1 -coro_tx=1 -coro_batch_size={nBatchSize} -verbose=1 -benchmark ycsb -threads 1 -scale_factor 10 -seconds 30 -log_data_dir /dev/shm/hodbadihi/ermia-log -log_buffer_mb=128 -log_segment_mb=16384 -parallel_loading -benchmark_options '-w C -r 10 -s 200000000 -t simple-coro'"

def getCollectHotSpotCMD(result_dir):
        return f"/opt/intel/oneapi/vtune/2025.0/bin64/vtune -collect hotspots -start-paused -result-dir {result_dir}"

def getReportHotSpotsCMD(result_dir):
    return f"/opt/intel/oneapi/vtune/2025.0/bin64/vtune -report hotspots -result-dir {result_dir} -report-output {result_dir}/report.txt"

def main():
    # Ensure the results directory exists
    hotspots_dir = "/specific/disk1/hodbadihi/MLP/corobase/scripts/results/hotspots"
    os.makedirs(hotspots_dir, exist_ok=True)


    dResultsStdOuts = {}
    lBatchesSizes = [ 1]
    sWantedFunctionName = "prefetch_full"
    nAttempts = 1

    for nBatchSize in lBatchesSizes:
        for nAttempt in range(nAttempts):
            sCurrentTime = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            sResultDir = os.path.join(hotspots_dir,f"batch_size_{nBatchSize}_{sCurrentTime}")
            sCollectHotSpotCMD = getCollectHotSpotCMD(sResultDir)
            sReportPath = os.path.join(sResultDir, 'report.txt')
            sErmiaCMD = getErmiaCommand(nBatchSize)
            sReportHotSpotsCMD = getReportHotSpotsCMD(sResultDir)
            # Concatenate HOTSPOTS_COMMAND with APP_COMMAND
            sCommand = f"{sCollectHotSpotCMD} {sErmiaCMD}"
            # Run the APP_COMMAND
            subprocess.run(sCommand, shell=True)
            subprocess.run(sReportHotSpotsCMD, shell=True)
            if nBatchSize not in dResultsStdOuts:
                dResultsStdOuts[nBatchSize] = {}  # Create an empty dictionary if it doesn't exist
            dResultsStdOuts[nBatchSize][nAttempt] = open(sReportPath).read()  # Read the report file content
    
    for nBatchSize in lBatchesSizes:
        for nAttempt in range(nAttempts):
            print(f"Batch size: {nBatchSize}, Attempt: {nAttempt}")
            nFunctionTime = ParseOutput(dResultsStdOuts[nBatchSize][nAttempt], sWantedFunctionName)
            print(f"\tTime for {sWantedFunctionName}: `{nFunctionTime}`[s]")
            


if __name__ == "__main__":
    
    main()


