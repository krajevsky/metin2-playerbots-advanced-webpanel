"""Host swap is sampled separately from RAM and survives zero/absent swap."""

import io
from types import SimpleNamespace

import collector


def test_host_metrics_reads_host_swap(monkeypatch):
    files = {
        "/host/proc/stat": "cpu 100 0 0 300 0 0 0 0\n",
        "/host/proc/meminfo": "MemTotal: 8388608 kB\nMemAvailable: 2097152 kB\nSwapTotal: 4194304 kB\nSwapFree: 3145728 kB\n",
        "/host/proc/loadavg": "1.0 0.8 0.5 1/100 1\n",
        "/host/proc/cpuinfo": "processor : 0\nprocessor : 1\n",
    }
    monkeypatch.setattr("builtins.open", lambda path, *args, **kwargs: io.StringIO(files[path]))
    monkeypatch.setattr(collector.os, "statvfs", lambda path: SimpleNamespace(f_blocks=100, f_bavail=40, f_frsize=1048576), raising=False)

    previous, cpu, ram_used, ram_total, disk_used, disk_total, swap_used, swap_total = collector.host_metrics()

    assert previous == (400, 300)
    assert cpu == 50.0
    assert (ram_used, ram_total) == (6144, 8192)
    assert (disk_used, disk_total) == (60, 100)
    assert (swap_used, swap_total) == (1024, 4096)


def test_swap_usage_handles_disabled_and_invalid_free_space():
    assert collector.swap_usage_mb({"SwapTotal": 0, "SwapFree": 0}) == (0, 0)
    assert collector.swap_usage_mb({"SwapTotal": 1024, "SwapFree": 2048}) == (0, 1)
