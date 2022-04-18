---
layout:     post
title:      "SPDK 실습 2 : 좋아 네 성능이 구라에 내 일(job) 모두하고 내 손모가지를 건다. 쫄리면 뒈지시던지."
date:       2022-05-19
author:     김 태훈 (thkim@gluesys.com)
categories: blog
tags:       [SPDK, NVMe, SSD, Flash, Memory, RDMA, Storage]
cover:      "/assets/SPDK_maincover.jpg"
main:       "/assets/SPDK_maincover.jpg"
---

※주의 레벨 5 이상 입장을 권장합니다※

안녕하세요. 이번 포스트에서는 SPDK 성능 리포트를 분석하고 실장비 성능 테스트를 통해 SPDK의 성능 이점을 직접 느껴보겠습니다.

## SPDK 성능 측정

SPDK는 새로운 버전을 공개할 때마다 커뮤니티에 최신 버전에 대한 성능 리포트([SPDK Performance Reports](https://spdk.io/doc/performance_reports.html))를 공개합니다. 성능 리포트는 크게 네 가지 항목으로 구성됩니다.
  - NVMe Bdev Performance Report 
  - NVMe-oF TCP Performance Report
  - NVMe-oF RDMA Performance Report
  - Vhost Performance Report
'NVMe Bdev Performance Report'는 SPDK에서 제공하는 Bdev 기능들에 대해서 성능을 측정하고 대중적으로 유사한 기능들과 성능을 비교하는 리포트입니다. 앞서 실습했던 논리 볼륨(lvol)의 성능 결과도 해당 리포트에서 확인할 수 있습니다.
'NVMe-oF TCP Performance Report'와 'NVMe-oF RDMA Performance Report'는 NVMe-oF 환경에서 NVMe SSD가 장착된 target가 연결할 host인 initiator를 구성하고 TCP와 RDMA 각각의 프로토콜로 연결했을 때 성능을 평가한 리포트 입니다. 마지막으로 'Vhost Performance Report'는 가상화 환경에서 Vhost 기술을 이용하여 SPDK에서 제공하는 NVMe SSD를 가상머신에 연결하여 성능을 평가한 리포트 입니다. 추가로 리포트를 작성한 시점에서 'Release 22.01' 버전에서는 'NVMe Bdev PCIe Gen4 Performance Report'이 추가되었는데, 이는 기존의 테스트는 PCIe Gen3로 테스트를 수행한 결과이며, 릴리즈 시점에 최신 버전의 PCIe 인터페이스인 Gen4의 등장으로 해당 인터페이스에서는 얼만큼의 성능 향상이 있는지 평가한 리포트 입니다.
그렇다면 SPDK에서는 어떤 방법으로 성능을 측정하는지 실습을 통해서 알아보겠습니다.

### 테스트 환경

CPU : Intel(R) Xeon(R) Silver 4210 CPU @ 2.20GHz * 2 sockets
Memory : Samsung DDR4 16GB Memory (2666MHz) * 2 EA (total memory : 32GB)
OS version : CentOS 7
Linux kernel version : 3.10.0-1127.19.1.el7.x86_64
SPDK version : SPDK 22.01
Fio version : 3.29
Storage
  - OS Disk : Seagate "2.5 1TB HDD (model : ST1000LM024)
  - NVMe SSD : Intel Optane SSD 900P Series 280GB PCIe 3.0 x4, NVMe (model : INTEL SSDPED1D280GA)

### 성능 측정 도구

SPDK 환경에서 성능 측정은 '`bdevperf`와 `fio`를 통해 수행할 수 있다. 먼저 `bdevperf`는 SPDK에서 자체적으로 제공하는 I/O 성능 측정 도구이며, SPDK에 최적화된 방법으로 I/O 테스트를 수행하는 도구이다. `bdevperf`는 SPDK 환경에서만 동작 가능하기 때문에 성능 리포트에서는 주로 fio 성능 측정 도구와 성능 비교에 사용된다. 다음으로 `fio`는 스토리지 분야에서는 널리 알려진 성능 측정 도구이며, 플러그인을 통해 테스트 환경에 맞는 I/O 기능을 적용할 수 있다. SPDK는 fio의 SPDK 플러그인을 제공하여 fio를 통해 SPDK 환경에서 NVMe SSD의 성능 테스트를 수행할 수 있도록 지원한다.

#### bdevperf

`bdevperf`성능 측정 도구는 `test/bdev/bdevperf`에 위치하며 간단한 테스트는 `test_config.sh` 스크립트를 통해 수행할 수 있습니다.

  ```
  [root@localhost spdk]# cd test/bdev/bdevperf
  [root@localhost bdevperf]# ls -l
  -rwxr-xr-x 1 root root 7740256 Jan 13 05:22 bdevperf
  -rw-r--r-- 1 root root   56826 Nov  1 06:27 bdevperf.c
  -rw-r--r-- 1 root root    1840 Jan 13 05:22 bdevperf.d
  -rw-r--r-- 1 root root  227480 Jan 13 05:22 bdevperf.o
  -rwxr-xr-x 1 root root    2910 Nov  1 06:27 bdevperf.py
  -rw-r--r-- 1 root root     587 Nov  1 06:27 common.sh
  -rw-r--r-- 1 root root     473 Nov  1 06:27 conf.json
  -rw-r--r-- 1 root root    2017 Nov  1 06:27 Makefile
  -rwxr-xr-x 1 root root    1257 Nov  1 06:27 test_config.sh
  [root@localhost bdevperf]# ./test_config.sh
  ...
  =============================================================
  Total                       : 2228736.00 IOPS    2176.50 MiB/s'
  22:44:02      -- bdevperf/common.sh@28 -- # grep -oE '[0-9]+'
  22:44:02       -- ./test_config.sh@39 -- # [[ 4 == \4 ]]
  22:44:02       -- ./test_config.sh@40 -- # cleanup
  22:44:02       -- bdevperf/common.sh@32 -- # rm -f /root/spdk/test/bdev/bdevperf/test.conf
  22:44:02       -- ./test_config.sh@41 -- # trap - SIGINT SIGTERM EXIT
  ```

테스트 수행 결과는 Total 행에 확인할 수 있으며, 성능에 필요한 옵션은 `bdevperf --help`에서 확인할 수 있습니다.
일반적으로 성능 측정 도구는 측정 대상을 지정해야 합니다. SPDK는 json 포맷의 파일로 측정할 대상을 정의합니다. `test_config.sh`에서 수행한 대상은 `conf.json`에 정의되어 있습니다.

  ```
  [root@localhost bdevperf]# cat conf.json
  {
    "subsystems": [
    {
      "subsystem": "bdev",
      "config": [
      {
        "method": "bdev_malloc_create",
        "params": {
          "name": "Malloc0",
          "num_blocks": 102400,
          "block_size": 512
        }
      },
      {
        "method": "bdev_malloc_create",
        "params": {
          "name": "Malloc1",
          "num_blocks": 102400,
          "block_size": 512
        }
      }
      ]
    }
    ]
  }
  ```

`conf.json` 파일을 확인해보면 각각 50MiB(512 * 102400) 용량을 갖는 ramdisk Malloc1과 Malloc2를 생성하는 설정입니다, 그렇다면 `test_config.sh`가 아닌 128 iodepth와 4KiB 블록 크기로 읽기 테스트를 300초 동안 수행하는 예제를 실행하겠습니다.

    ```
    [root@localhost bdevperf]# ./bdevperf -t 300 -c ./conf.json -q 128 -o 4096 -w read
    [2022-01-13 22:47:33.489389] Starting SPDK v22.01-pre git sha1 ed8be4ad0 / DPDK 21.08.0 initialization...
    [2022-01-13 22:47:33.489561] [ DPDK EAL parameters: [2022-01-13 22:47:33.489591] bdevperf [2022-01-13 22:47:33.489612] --no-shconf [2022-01-13 22:47:33.489635] -c 0x1 [2022-01-13 22:47:33.489656] --log-level=lib.eal:6 [2022-01-13 22:47:33.489676] --log-level=lib.cryptodev:5 [2022-01-13 22:47:33.489697] --log-level=user1:6 [2022-01-13 22:47:33.489718] --iova-mode=pa [2022-01-13 22:47:33.489739] --base-virtaddr=0x200000000000 [2022-01-13 22:47:33.489761] --match-allocations [2022-01-13 22:47:33.489781] --file-prefix=spdk_pid174830 [2022-01-13 22:47:33.489804] ]
    EAL: No available 1048576 kB hugepages reported
    EAL: No free 2048 kB hugepages reported on node 1
    TELEMETRY: No legacy callbacks, legacy socket not created
    [2022-01-13 22:47:33.593973] app.c: 543:spdk_app_start: *NOTICE*: Total cores available: 1
    [2022-01-13 22:47:33.880832] reactor.c: 943:reactor_run: *NOTICE*: Reactor started on core 0
    [2022-01-13 22:47:33.881331] accel_engine.c:1012:spdk_accel_engine_initialize: *NOTICE*: Accel engine initialized to use software engine.
    Running I/O for 300 seconds...
    Job: Malloc0 (Core Mask 0x1)
    Malloc0             :  407177.81 IOPS    1590.54 MiB/s
    Job: Malloc1 (Core Mask 0x1)
    Malloc1             :  407177.81 IOPS    1590.54 MiB/s
    =============================================================
    Total                       :  814355.63 IOPS    3181.08 MiB/s
    ```

위 결과처럼 ramdisk Malloc0과 Malloc1에서 814,355 IOPS와 3181 MiB/s의 읽기 성능을 확인할 수 있습니다.
이번에는 ramdisk가 아닌 실제 NVMe SSD의 성능을 측정해보겠습니다. 마찬가지로 테스트 대상을 json 포맷의 파일로 정의해야 하는데, 이는 `scripts/get_nvme.sh` 스크립트를 사용하여 간편하게 구성할 수 있습니다.

  ```
  [root@localhost bdevperf]# /root/spdk/scripts/gen_nvme.sh --json-with-subsystems | jq . > nvme.json
  [root@localhost bdevperf]# cat nvme.json
  {
    "subsystems": [
    {
      "subsystem": "bdev",
      "config": [
      {
        "method": "bdev_nvme_attach_controller",
        "params": {
          "trtype": "PCIe",
          "name": "Nvme0",
          "traddr": "0000:3b:00.0"
        }
      }
      ]
    }
    ]
  }
  ```

완성된 `nvme.json` 파일로 `bdevperf`를 수행해보겠습니다. `-c` 옵션의 파일 경로만 변경하고 나머지 옵션은 동일하게 설정합니다.

  ```
  [root@localhost bdevperf]# ./bdevperf -t 300 -c ./nvme.json -q 128 -o 4096 -w read
  [2022-01-13 23:15:52.588048] Starting SPDK v22.01-pre git sha1 ed8be4ad0 / DPDK 21.08.0 initialization...
  [2022-01-13 23:15:52.588245] [ DPDK EAL parameters: [2022-01-13 23:15:52.588276] bdevperf [2022-01-13 23:15:52.588297] --no-shconf [2022-01-13 23:15:52.588319] -c 0x1 [2022-01-13 23:15:52.588354] --log-level=lib.eal:6 [2022-01-13 23:15:52.588375] --log-level=lib.cryptodev:5 [2022-01-13 23:15:52.588396] --log-level=user1:6 [2022-01-13 23:15:52.588417] --iova-mode=pa [2022-01-13 23:15:52.588439] --base-virtaddr=0x200000000000 [2022-01-13 23:15:52.588460] --match-allocations [2022-01-13 23:15:52.588481] --file-prefix=spdk_pid241533 [2022-01-13 23:15:52.588503] ]
  EAL: No available 1048576 kB hugepages reported
  EAL: No free 2048 kB hugepages reported on node 1
  TELEMETRY: No legacy callbacks, legacy socket not created
  [2022-01-13 23:15:52.683909] app.c: 543:spdk_app_start: *NOTICE*: Total cores available: 1
  [2022-01-13 23:15:52.951868] reactor.c: 943:reactor_run: *NOTICE*: Reactor started on core 0
  [2022-01-13 23:15:52.952347] accel_engine.c:1012:spdk_accel_engine_initialize: *NOTICE*: Accel engine initialized to use software engine.
  Running I/O for 300 seconds...
  Job: Nvme0n1 (Core Mask 0x1)
  Nvme0n1             :  334248.13 IOPS    1305.66 MiB/s
  =============================================================
  Total                       :  334248.13 IOPS    1305.66 MiB/s
  ```

SPDK 드라이버로 연결된 Intel Optane 900P 280GB NVMe SSD의 single core, 128 iodepth, 4KiB 읽기 성능은 334,248 IOPS, 1305 MiB/s 로 확인되었습니다.

#### FIO 테스트

Fio[^6]는 오픈소스로 구현된 가장 대중적인 스토리지 성능 측정 도구입니다. 특히 fio는 다양한 스토리지 스택에서 테스트를 수행할 수 있도록 플러그인 기능을 제공합니다. SPDK는 fio의 플러그인을 제공하며, 이를 통해 다양한 프레임워크(e.g. 리눅스 커널 스택:LIO)와의 성능 비교도 가능하게 합니다.

fio 성능 테스트를 위해서 [github](https://github.com/axboe/fio)의 최신 버전의 코드를 다운받습니다. fio 빌드를 위해서는 높은 버전의 gcc 패키지가 필요합니다. 현재 centos 7 기준으로 gcc 업데이트가 필요합니다. gcc 업데이트는 [링크](https://m.blog.naver.com/alice_k106/221019680668)를 참고합니다.

  ```
  [root@localhost ~]# git clone https://github.com/axboe/fio
  [root@localhost ~]# cd fio
  [root@localhost fio]# make -j 40
  ...
  LINK t/read-to-pipe-async
  LINK t/fio-btrace2fio
  LINK t/io_uring
  [root@localhost fio]# ls -l fio
  -rwxr-xr-x 1 root root 6400472 Jan 13 23:45 fio
  [root@localhost fio]# ./fio --version
  fio-3.29-7-g01686
  ```

fio 빌드가 완료되면 SPDK의 ./configure에서 `--with-fio=<FIO_PATH>` 옵션을 추가하고 리빌드 합니다.

  ```
  [root@localhost fio]# cd ~/spdk
  [root@localhost spdk]# ./configure --with-fio=/root/fio
  Notice: ISA-L, compression & crypto require NASM version 2.14 or newer. Turning off default ISA-L and crypto features.
  Using default SPDK env in /root/spdk/lib/env_dpdk
  Using default DPDK in /root/spdk/dpdk/build
  Creating mk/config.mk...done.
  Creating mk/cc.flags.mk...done.
  [root@localhost spdk]# make -j 40
  ...
  CXX test/cpp_headers/string.o
  CXX test/cpp_headers/gpt_spec.o
  CXX test/cpp_headers/nvme_ocssd.o
  LINK dif_ut
  LINK ftl_wptr_ut
  LINK ftl_io_ut
  ```

빌드가 완료되면 `build/fio` 경로에 fio 플러그인 파일이 생성되어 있습니다. fio 플러그인 코드를 `examples/bdev/fio_plugin`에 위치합니다. 해당 위치에는 fio 테스트를 위한 다양한 예제들이 존재합니다.

  ```
  [root@localhost spdk]# ls build/fio
  total 12852
  -rwxr-xr-x 1 root root 8665272 Jan 13 23:49 spdk_bdev
  -rwxr-xr-x 1 root root 4490272 Jan 13 23:49 spdk_nvme
  [root@localhost spdk]# cd examples/bdev/fio_plugin
  [root@localhost fio_plugin]# ls -l
  total 304
  -rw-r--r-- 1 root root    282 Nov  1 06:27 bdev.json
  -rw-r--r-- 1 root root    522 Nov  1 06:27 bdev_zoned.json
  -rw-r--r-- 1 root root    253 Jan 20 22:12 example_config.fio
  -rw-r--r-- 1 root root  33173 Nov  1 06:27 fio_plugin.c
  -rw-r--r-- 1 root root   5052 Jan 21 01:34 fio_plugin.d
  -rw-r--r-- 1 root root 220056 Jan 21 01:34 fio_plugin.o
  -rw-r--r-- 1 root root    320 Nov  1 06:27 full_bench.fio
  -rw-r--r-- 1 root root   1933 Nov  1 06:27 Makefile
  -rw-r--r-- 1 root root   8253 Nov  1 06:27 README.md
  -rw-r--r-- 1 root root    314 Jan 21 00:55 run_fio.fio
  -rw-r--r-- 1 root root    255 Nov  1 06:27 zbd_example.fio
  ```

완성된 fio 플러그인으로 fio를 수행해보겠습니다. `bdevperf`와 마찬가지로 성능 측정 대상 설정을 위해 json 포맷의 구성 파일을 생성해야 합니다.

  ```
  [root@localhost fio_plugin]# /root/spdk/scripts/gen_nvme.sh --json-with-subsystems | jq . > nvme.json
  [root@localhost fio_plugin]# cat nvme.json
  {
    "subsystems": [
    {
      "subsystem": "bdev",
        "config": [
        {
          "method": "bdev_nvme_attach_controller",
          "params": {
            "trtype": "PCIe",
            "name": "Nvme0",
            "traddr": "0000:3b:00.0"
          }
        }
        ]
    }
    ]
  }
  ```

이 떄, fio 성능 측정을 수행할 때 입력한 json 파일을 기반으로 테스트할 장치를 자동 구성하기 때문에 연결된 장치가 있다면 미리 해제해야 합니다. 참고로 lvol과 lvstore를 생성한 상태라면 해제 이전에 모두 삭제한 후 `bdev_nvme_detach_controller`를 수행해야 합니다. 테스트 대상에 lvol 또는 lvstore가 존재할 경우 fio 수행 시 관련 에러가 확인될 수 있습니다.

  ```
  [root@localhost fio_plugin]# scripts/rpc.py bdev_nvme_detach_controller NVMe0
  [root@localhost fio_plugin]# scripts/rpc.py bdev_nvme_get_controllers
  []
  ```

모든 준비가 완료되었으면 fio 테스트 옵션을 설정해보겠습니다. fio 테스트 옵션은 [spdk performance report 21.10](https://ci.spdk.io/download/performance-reports/SPDK_nvme_bdev_perf_report_2110.pdf)의 'Test Case 1'의 설정을 참고하겠습니다.
  ```
  [root@localhost fio_plugin]# cat << EOF > run_fio.fio
  [global]
  ioengine=/root/spdk/build/fio/spdk_bdev
  spdk_json_conf=/root/spdk/examples/bdev/fio_plugin/nvme.json

  gtod_reduce=1
  direct=1
  thread=1
  norandommap=1
  time_based=1
  ramp_time=60s
  runtime=300s
  rw=read
  bs=4k
  numjobs=1

  [filename0]
  filename=Nvme0n1
  iodepth=128
  EOF

  [root@localhost fio_plugin]# /root/fio/fio ./run_fio.fio
  filename0: (g=0): rw=read, bs=(R) 4096B-4096B, (W) 4096B-4096B, (T) 4096B-4096B, ioengine=spdk_bdev, iodepth=128
  fio-3.29-7-g01686
  Starting 1 thread
  [2022-01-20 22:49:33.573673] Starting SPDK v22.01-pre git sha1 ed8be4ad0 / DPDK 21.08.0 initialization...
  [2022-01-20 22:49:33.573890] [ DPDK EAL parameters: [2022-01-20 22:49:33.573922] fio [2022-01-20 22:49:33.573944] --no-shconf [2022-01-20 22:49:33.573965] -c 0x1 [2022-01-20 22:49:33.573986] --log-level=lib.eal:6 [2022-01-20 22:49:33.574007] --log-level=lib.cryptodev:5 [2022-01-20 22:49:33.574027] --log-level=user1:6 [2022-01-20 22:49:33.574062] --iova-mode=pa [2022-01-20 22:49:33.574082] --base-virtaddr=0x200000000000 [2022-01-20 22:49:33.574103] --match-allocations [2022-01-20 22:49:33.574124] --file-prefix=spdk_pid269971 [2022-01-20 22:49:33.574145] ]
  EAL: No available 1048576 kB hugepages reported
  EAL: No free 2048 kB hugepages reported on node 1
  TELEMETRY: No legacy callbacks, legacy socket not created
  [2022-01-20 22:49:33.707015] accel_engine.c:1012:spdk_accel_engine_initialize: *NOTICE*: Accel engine initialized to use software engine.
  Jobs: 1 (f=1): [R(1)][100.0%][r=2602MiB/s][r=666k IOPS][eta 00m:00s]
  filename0: (groupid=0, jobs=1): err= 0: pid=270034: Thu Jan 20 22:55:33 2022
    read: IOPS=666k, BW=2603MiB/s (2730MB/s)(763GiB/300001msec)
      bw (  MiB/s): min= 2567, max= 2614, per=100.00%, avg=2604.31, stdev= 7.14, samples=600
      iops        : min=657376, max=669316, avg=666702.32, stdev=1828.62, samples=600
    cpu          : usr=100.00%, sys=0.00%, ctx=724, majf=0, minf=139
    IO depths    : 1=0.0%, 2=0.0%, 4=0.0%, 8=0.0%, 16=0.0%, 32=0.0%, >=64=100.0%
      submit    : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
      complete  : 0=0.0%, 4=100.0%, 8=0.1%, 16=0.1%, 32=0.1%, 64=0.1%, >=64=0.1%
      issued rwts: total=199938792,0,0,0 short=0,0,0,0 dropped=0,0,0,0
      latency   : target=0, window=0, percentile=100.00%, depth=128

  Run status group 0 (all jobs):
    READ: bw=2603MiB/s (2730MB/s), 2603MiB/s-2603MiB/s (2730MB/s-2730MB/s), io=763GiB (819GB), run=300001-300001msec
  ```

fio 옵션은 `bdevperf`와 유사하게 single thread, 128 iodepth, 4KiB 읽기 테스트를 수행하는 예시이며, 측정 결과 666k IOPS 및 2603MiB/s 읽기 성능을 확인할 수 있습니다.

  * 참고
    - https://github.com/spdk/spdk/tree/master/examples/nvme/fio_plugin
    - https://www.intel.com/content/www/us/en/developer/articles/technical/evaluate-performance-for-storage-performance-development-kit-spdk-based-nvme-ssd.html
    - https://github.com/spdk/spdk/issues/1104

#### 실시간 모니터링 방법

마지막으로 SPDK에 등록된 장치의 입출력 상황을 모니터링하는 방법으로 실습을 마치겠습니다. SPDK에 등록된 NVMe SSD는 커널에 오너쉽이 존재하지 않기 때문에 일반적으로 리눅스에서 제공하는 iostat, dstat과 같은 툴로는 확인할 수 없습니다. SPDK는 생성된 NVMe 또는 bdev 장치를 모니터링할 수 있는 간단한 스크립트를 제공합니다. 모니터링 스크립트는 `scripts/iostat.py`에 위치합니다.

  ```
  [root@localhost spdk]# ls -l scripts/
  -rwxr-xr-x 1 root root 16435 Nov  1 06:27 scripts/iostat.py
  [root@localhost spdk]# scripts/iostat.py
  cpu_stat:  user_stat  nice_stat  system_stat  iowait_stat  steal_stat  idle_stat
   3.16%      0.00%      2.57%        0.62%        0.00%       93.65%

   Device   tps   KB_read/s  KB_wrtn/s  KB_dscd/s  KB_read  KB_wrtn  KB_dscd
   NVMe0n1  0.00  0.00       0.00       0.00       36.00    0.00     0.00
  ```

이름에서 알 수 있듯이 iostat와 유사한 정보를 출력합니다. NVMe SSD의 namespace 외에도 lvol 등 bdev로 등록된 장치의 상태도 출력할 수 있습니다. 이때 `-i` 옵션으로 interval을 설정할 수 있으며 interval 입력 시 반드시 전체 수행할 시간(`-t`)를 입력해야 합니다.

  ```
  [root@localhost spdk]#scripts/iostat.py -i 1 -t 100
  cpu_stat:  user_stat  nice_stat  system_stat  iowait_stat  steal_stat  idle_stat
  5.57%      0.00%      4.57%        0.00%        0.00%       89.86%

  Device                                tps   KB_read/s  KB_wrtn/s  KB_dscd/s  KB_read  KB_wrtn  KB_dscd
  11c7cb7c-4a34-494a-aead-7225be36ff3e  0.00  0.00       0.00       0.00       0.00     0.00     0.00
  875d15bd-5a4b-479a-953a-06c35eb0b140  0.00  0.00       0.00       0.00       0.00     0.00     0.00
  479e14e8-9b8d-4a53-b330-a687f81cb9ff  0.00  0.00       0.00       0.00       0.00     0.00     0.00
  70e39e3a-8e68-4838-b158-d2162804eb92  0.00  0.00       0.00       0.00       0.00     0.00     0.00
  NVMe0n1                               0.00  0.00       0.00       0.00       0.00     0.00     0.00
  ```

아쉽게도 `bdevperf`와 `fio` 수행 도중에는 확인할 수 없습니다. 이는 장치가 `spdk_tgt`이 아닌 bdevperf와 fio가 수행되는 유저 프로세스에 오너쉽이 존재하기 때문입니다. 마찬가지로 성능 측정 도구를 수행할 때 연결된 NVMe SSD 컨트롤러를 해제하는 이유도 장치의 오너쉽이 `spdk_tgt`에 존재하기 때문에 성능 측정 도구에서 해당 장치를 사용할 수 없기 때문입니다.

&nbsp;

마치며
-----

끝내는 말(You Died)

&nbsp;

각주
---

[^1]: vfio
[^2]: uio
[^3]: rpc
[^4]: system-call
[^5]: cuse
[^6]: fio
