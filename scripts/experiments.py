
from CExperimentManager.CExperimentManager import CExperimentManager
from CExperimentManager.CMetric import CMetric
from CExperimentManager.CExperimentData import CExperimentData


def GetMetricsList():
    lMetrics = []
    lMetrics.append(CMetric("Total Cycles", '(\d{1,3}(?:,\d{3})*)\s+cycles', 1))
    lMetrics.append(CMetric("Total Stalls", '(\d{1,3}(?:,\d{3})*)\s+cycle_activity.stalls_l3_miss',1))
    lMetrics.append(CMetric("Throughput", 'agg_throughput: (\d+) ops\/sec',1))
    return lMetrics

def GetExperimentsList():
    lExperiments = []
    lBatchesSizes = [ 1,2,3,4,5,7,9,11,13,15,17,19]
    sProgramPath = '/specific/disk1/hodbadihi/MLP/corobase/build/ermia_SI'

    for nBatchSize in lBatchesSizes:
        sCmd = f'{sProgramPath} -physical_workers_only=1 -index_probe_only=1 -node_memory_gb=50 -null_log_device=1 -coro_tx=1 -coro_batch_size={nBatchSize} -verbose=1 -benchmark ycsb -threads 1 -scale_factor 10 -seconds 20 -log_data_dir /dev/shm/hodbadihi/ermia-log -log_buffer_mb=128 -log_segment_mb=16384 -parallel_loading -enable_perf=1 -benchmark_options "-w C -r 10 -s 100000000 -t simple-coro"'
        sName = f'{nBatchSize}-simple-coro'
        lExperiments.append(CExperimentData(sName, sCmd))

    return lExperiments

if __name__ == "__main__":

    lMetrics = GetMetricsList()
    lExperiments = GetExperimentsList()

    ExperimentManager = CExperimentManager(lExperiments,lMetrics,"results.csv")
    ExperimentManager.Run()

