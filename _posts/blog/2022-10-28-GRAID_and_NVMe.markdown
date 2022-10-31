---
layout:     post
title:      "NVMe 시대의 RAID: GRAID와 PoseidonOS"
date:       2022-10-28
author:     박현승 (hspark0582@gluesys.com)
categories: blog
tags:       [RAID, NVMe, SSD, GRAID, SupremeRAID, PoseidonOS, SPDK]
cover:      "/assets/graid_and_nvme/orig.jpg"
main:       "/assets/graid_and_nvme/cut.png"
---

다른 컴퓨터 부품과 마찬가지로 스토리지 장치 역시 영원히 문제없이 작동할 수는 없습니다. 잠시 사용자의 요청에 반응하지 못한다거나, 모르는 사이 저장된 자료의 내용이 바뀌어 있기도 하고, 최종적으로는 수명을 다하면 작동을 멈추게 됩니다. 이러한 스토리지 장치의 문제로부터 사용자의 자료를 보호하는 기술은 스토리지 자체와 역사를 같이 했습니다. 가장 대표적인 기술로 Redundant Array of Independent Disks (**[RAID](https://tech.gluesys.com/blog/2020/07/22/storage_6_intro.html)**)가 있는데, RAID는 여러 개의 저장 장치를 하나로 묶어 해당 장치 중 일부가 사용 불가능하게 되더라도 데이터가 손실되지 않도록 하는 기법을 말합니다. RAID에서는 데이터의 안전한 보관을 위해 데이터 복제 방식(RAID-1)과 패리티 블록을 추가로 저장하는 방식(RAID-5, 6)을 제공합니다.

이 RAID는 탄생 후 대부분의 시간을 하드 디스크 드라이브(HDD)와 함께했습니다. 그러나 시간이 흘러 SSD(Solid State Drive)가 HDD를 점차 대체해 나가고, 그에 맞춰 기존의 SCSI나 SATA보다 빠른 저장장치 연결 표준인 [NVMe](https://tech.gluesys.com/blog/2021/03/03/NVMe_1.html)가 등장하면서, RAID에도 변화가 생기기 시작했습니다. 이번 포스트에서는 기존의 방식이 왜 NVMe SSD에는 적합하지 않은지, 이를 해결하기 위해 어떤 기법들이 생겨났는지 알아보도록 하겠습니다.

&nbsp;

## 기존 하드웨어 RAID

RAID를 구성하는 방법에는 크게 두 가지가 있는데, 하드웨어 RAID와 소프트웨어 RAID입니다. 이 중 하드웨어 RAID는 별도의 장비가 필요하여 설치가 불편하지만, 소프트웨어 RAID에 비해 좋은 성능을 보여줘 보편적으로 사용되어 왔습니다. 하드웨어 RAID는 주로 전용 컨트롤러를 PCIe 슬롯에 장착한 후 디스크를 컨트롤러에 직접 연결하고, RAID 컨트롤러가 운영체제에 인터페이스를 제공합니다. RAID 컨트롤러는 인터페이스를 통해 들어온 I/O 명령을 해석 및 변환한 뒤 해당하는 저장 장치에 전달하고, 돌아온 결과를 운영체제에 반환하는 방식으로 동작합니다. 이러한 방식에서는 I/O 종류(읽기, 쓰기)와 관계없이 모든 명령과 데이터가 RAID 컨트롤러를 거쳐 가게 됩니다.

저장 장치로 HDD를 사용할 경우 이러한 구성이 문제가 되지 않습니다. HDD의 명령어 처리 속도(IOPS)와 대역폭은 NVMe SSD에 비해 상대적으로 매우 느려 적당한 성능의 컨트롤러와 단일 PCIe 슬롯으로도 충분히 많은 수의 HDD를 큰 무리 없이 작동시킬 수 있기 때문입니다.

&nbsp;

![Photo of Broadcom MegaRAID SAS 9361-24i](/assets/graid_and_nvme/megaraid_24i.jpg){: width="600"}

![Screenshot of result after executing mdadm --detail](/assets/graid_and_nvme/mdadm_detail2.png){: width="600"}

<center> 위: 하드웨어 RAID 장비 중 하나인 Broadcom MegaRAID SAS 9361-24i </center>

<center> 아래: 리눅스 커널 내장 소프트웨어 RAID 프로그램인 mdadm을 사용한 RAID6 드라이브의 구성 화면 </center>

&nbsp;

## GRAID

그러나 NVMe SSD가 보급되면서 사정은 달라집니다. 기존 컨트롤러는 SSD 수십 대의 명령어 처리 속도를 따라갈 수 없고, 컨트롤러 업그레이드로 성능을 따라간다 한들 이미 NVMe SSD 1대가 PCIe의 대역폭을 모두 사용하는 상황에서 모든 데이터가 컨트롤러를 거쳐 가는 기존 방식이 SSD의 성능을 100% 보여줄 리 만무하기 때문입니다. 위 사진의 MegaRAID 장비의 경우, 호스트와는 64Gbps의 속도로, SAS 장치와는 총 288Gbps의 속도로 통신할 수 있습니다. HDD라면 대부분의 경우 차고 넘치는 성능이지만, NVMe SSD의 경우 대당 56Gbps (7GB/s)의 순차 읽기 성능을 내는 것이 어렵지 않음을 생각하면 다른 접근 방법의 필요성은 명백하다 할 수 있겠습니다.

&nbsp;

![Photo of GRAID SR1010](/assets/graid_and_nvme/SR1010.png){: width="600"}

<center> GRAID사의 SupremeRAID SR-1010 제품 (출처: GRAID Technology) </center>

&nbsp;

위 문제들을 해결하기 위해 [GRAID Technology](https://www.graidtech.com/)에서 SupremeRAID라는 이름의 새로운 RAID 컨트롤러를 출시하였습니다. GRAID라는 이름과 위 사진의 모습에서 눈치를 채셨을 수도 있지만 이 SupremeRAID 장치는 GPU를 RAID 연산 장치로 사용합니다. 기존 RAID 컨트롤러에 들어가던 ASIC 등의 커스텀 칩을 NVMe SSD에 맞게 고성능으로 만드는 것보다 NVIDIA RTX A2000 등의 GPU를 사용해버리는 것이 더 경제적이라고 하니, NVMe SSD의 성능 차이가 어느 정도인지 실감할 수 있습니다. 이 연산 성능 덕분에, SupremeRAID의 무작위 읽기 작업 IOPS는 기존 하드웨어 RAID 장비에 비해 약 4배, 소프트웨어 RAID에 비해서는 약 8배에 달합니다.

또 다른 문제점이었던 부족한 대역폭을 해결하기 위해 SupremeRAID는 다른 접근법을 사용하였습니다. 저장 장치들은 더 이상 컨트롤러에 연결되지 않고, 하드웨어 RAID를 사용하지 않았을 때와 마찬가지로 호스트 서버에 직접 연결됩니다. 별다른 설정을 하지 않았다면 운영체제는 NVMe SSD 장비를 GRAID가 연결되지 않았을 때와 마찬가지로 직접 접근할 수 있고, 설정을 하게 되면 관리만 SupremeRAID 장비가 할 뿐, 데이터는 그대로 운영체제가 직접 SSD에서 가져오게 됩니다. 그 덕분에, 쓰기 작업의 경우 패리티 생성을 위해 컨트롤러를 거치지만, 최소한의 주소 변환 작업만이 필요한 읽기 작업을 수행할 때는 데이터를 바로 불러올 수 있어 최대 110GB/s의 속도를 낼 수 있습니다.

&nbsp;

![Data flowchart of GRAID, HW RAID, and SW RAID](/assets/graid_and_nvme/graid_pic_a012.jpg){: width="600"}

![GRAID performance comparison](/assets/graid_and_nvme/GRAID-Competitive-knockoff.webp){: width="600"}

<center> 위: GRAID SupremeRAID와 기존 하드웨어 RAID, 소프트웨어 RAID의 작동 개요 (출처: HPC TECH) </center>

<center> 아래: SupremeRAID와 기존 소프트웨어, 하드웨어 RAID 솔루션의 성능 비교 자료 (출처: GRAID Technology) </center>

&nbsp;

## PoseidonOS

또 다른 솔루션으로는 삼성이 주도하고 있는 오픈소스 프로젝트인 [PoseidonOS](https://poseidonos.io/)가 있습니다. 기존 소프트웨어 RAID의 경우 저장 장치의 종류에 관계 없이 모두 다 같은 블록 디바이스로 취급하는 반면 PoseidonOS는 [SPDK](https://spdk.io/)를 사용하여 NVMe SSD에 최적화되어 있습니다. SPDK는 NVMe 장비를 기존 블록 디바이스 인터페이스보다 더욱 효율적으로 사용하기 위해 개발되고 있는 도구와 라이브러리 모음으로, 자세한 내용은 [이전 포스트](https://tech.gluesys.com/blog/2022/02/18/SPDK_1.html)를 참조 부탁드리겠습니다. PoseidonOS는 이 SPDK를 사용해 애플리케이션으로부터 SSD까지의 입출력 스택을 모두 유저 영역에 구현하여 커널 레벨과 유저 레벨 간 컨텍스트 스위치나 데이터 복사에 소요되는 시간을 없애고, 이외에도 I/O 폴링이나 hugepage 등을 통해 성능을 향상시켰습니다.

PoseidonOS는 현재 공식적으로 Ubuntu 18.04 버전만 지원하고 있으나, CentOS Stream 8이나 Rocky Linux 8과 같은 배포판에서도 구동이 가능하도록 저희 글루시스가 이식 작업을 진행하였습니다. 지난 18일 해당 내용이 메인 브랜치에 병합되었으므로 ([병합 커밋](https://github.com/poseidonos/poseidonos/commit/98f9e0171f70da186c1db74236aa35e549ac21fe)) 다음 릴리즈에서는 더욱 다양한 환경에서 PoseidonOS를 사용할 수 있을 것 같습니다.

&nbsp;

![Kernel-level vs User-level I/O stack](/assets/graid_and_nvme/user_vs_kernel.png){: width="600"}

<center> 커널 레벨 입출력 스택과 유저 레벨 입출력 스택의 비교 (출처: PoseidonOS 홈페이지) </center>

&nbsp;

PoseidonOS는 아래와 같은 다양한 기능들을 탑재하여 제공하고 있습니다.

* RAM 사용 I/O 버퍼
* RAID 레벨: 0, 5, 6, 10 (RAID 레벨 6의 경우, [지난 2022년 8월에 커밋되어](https://github.com/poseidonos/poseidonos/pull/298) 아직 정식 릴리즈는 되지 않았습니다.)
* RAID 스페어 디바이스
* QoS: 최소 및 최대 성능 (IOPS, 대역폭) 설정
* NVMe-oF 이니시에이터 형태로 제공 (NVMe-oF를 거치지 않는 일반 블록 디바이스 생성은 집필 시점 기준 미구현)
* 텔레메트리 수집 및 제공 (API, [웹 UI](https://github.com/poseidonos/poseidonos-gui))

이 중 QoS는 하나의 노드를 여러 클라이언트나 애플리케이션이 나누어 쓰는 경우에도 일정한 성능을 보장하기 위한 기술입니다. 일반적으로 노드가 처리할 수 있는 최대 성능 이상으로 요청이 많아지면 그에 비례하여 모든 클라이언트가 느려지게 됩니다. 최소 성능을 설정하면 그러한 상황에서도 지정한 클라이언트는 설정된 최소 성능(대역폭, IOPS)을 계속하여 사용할 수 있게 되고, 반대로 서비스 우선 순위가 낮은 클라이언트에 최대 성능 제한을 설정하여 다른 클라이언트가 사용할 대역폭이 소진되지 않도록 할 수 있습니다.

&nbsp;

## 간단 성능 측정

위에서 소개한 SupremeRAID와 PoseidonOS의 성능을 실제로 알아보고자 벤치마크를 수행해 보았습니다. 여건상 충분한 수의 SSD를 사용할 수 없어 위에서 말한 장점을 돋보이게 해줄 수는 없지만, NVMe SSD와 이들을 사용한 RAID 솔루션이 기존 SAS HDD RAID 대비 어느 정도의 성능을 보여줄 수 있는지 감을 잡는 데 도움이 되었으면 합니다. 자세한 벤치마크 환경은 다음과 같습니다.

&nbsp;

| 종류 | 장비명 |
| :--- | :--- |
| CPU | Intel Xeon Silver 4310 CPU @ 2.10GHz x 2 |
| 메모리 | SK Hynix HMA82GR7DJR8N-XN 3200MHz 16G x 8 |
| SSD | Samsung MZVL21T0HCLR-00B00 (PM9A1) x 4 |
| OS | Rocky Linux 8.6 |

<details>
    <summary>fio 설정 파일</summary>

    [global]
    direct=1
    ioengine=libaio
    iodepth=16
    numjobs=32
    randrepeat=0
    kb_base=1000
    filename=/dev/nvme0n1
    size=128GiB
    group_reporting=1
    cpus_allowed_policy=split
    cpus_allowed=0-31
    ramp_time=5s
    runtime=3m
    time_based=1
    wait_for_previous

    [seqread]
    blocksize=1MiB
    readwrite=read

    [seqwrite]
    blocksize=1MiB
    readwrite=write

    [randread4]
    blocksize=4KiB
    readwrite=randread

    [randwrite4]
    blocksize=4KiB
    readwrite=randwrite

    [randread128]
    blocksize=128KiB
    readwrite=randread

    [randwrite128]
    blocksize=128KiB
    readwrite=randwrite
</details>

&nbsp;

성능 측정은 삼성 M.2 SSD 4대를 RAID6로 묶어 진행하였습니다. 본래 7,000MB/s의 순차 읽기 성능을 낼 수 있는 모델이지만, 성능 측정을 진행한 장비의 메인보드가 PCIe 4.0을 지원하지 않아 아래와 같이 약 절반의 성능에 그쳤습니다. PoseidonOS는 생성한 RAID 디바이스를 직접 사용할 수 없어 NVMe-oF 이니시에이터를 생성 후 이를 같은 장비에서 연결하여 측정하였습니다. GRAID SupremeRAID는 생성된 가상 장치를 직접 한 번, 그리고 PoseidonOS와 같은 방식으로 다시 한번 측정하여 비교해 보았습니다.

&nbsp;

| block size & I/O type | single device | GRAID SupremeRAID (direct) | GRAID SupremeRAID (NVMe-oF) | PoseidonOS |
| :--- | :--- | :--- | :--- | :--- |
| 1MiB seq. read (MiB/s) | 3370.9 | 6771.7 | 6725.2 | 3632.4 |
| 1MiB seq. write (MiB/s) | 1771.2 | 4443.9 | 4526.1 | 1028.8 |
| 4KiB random read (MiB/s) | 3006.5 | 9356.5 | 3147.1 | 930.30 |
| 4KiB random write (MiB/s) | 1912.7 | 2511.6 | 2400.2 | 309.44 |
| 128KiB random read (MiB/s) | 3345.7 | 6817.6 | 6577.0 | 2831.8 |
| 128KiB random write (MiB/s) | 2036.6 | 5631.0 | 5269.9 | 971.01 |

&nbsp;

![Graph of above table](/assets/graid_and_nvme/bench_graph.png){: width="600"}

&nbsp;

먼저 대부분의 경우 SupremeRAID가 단일 장비의 두 배 또는 그 이상의 성능을 보이는 것을 확인할 수 있습니다. 이는 RAID6를 사용하였음을 감안하면 성능 손실이 거의 일어나지 않았다는 것을 의미합니다. 반면, PoseidonOS의 경우 NVMe-oF를 거쳤음을 감안해도 SupremeRAID보다 그다지 좋은 지표를 보여주지 못하였는데, 추가적인 하드웨어 장비를 사용하지 않는 소프트웨어 RAID라는 특성상 불가피하다고 볼 수 있겠습니다. 또한 NVMe-oF의 사용 유무에 따른 성능 차이를 비교해 볼 수 있겠습니다. 앞서 말씀드린 것과 같이 위의 두 GRAID 성능 측정 결과는 같은 가상 장비를 직접 사용한 것과 NVMe-oF를 사용한 것으로, 서버-클라이언트 간의 통신 하드웨어 성능에 관계없이 순수하게 NVMe-oF 레이어에서의 손실만을 볼 수 있습니다. 두 값의 차이는 I/O 블록 크기의 영향을 가장 크게 받아 블록 크기가 1MiB인 경우 실험 오차 내의 동일한 성능을 보여주었습니다. 128MiB의 경우 약간의 손실만이 있었지만, 4KiB 블록 읽기 성능은 약 3분의 1로 떨어진 것을 확인할 수 있습니다.

&nbsp;

## 마치며

RAID 기술은 데이터 보전과 서비스 가용성을 위해 이전부터 지금까지 널리 사용되어 왔지만, 저장장치가 빨라지고 대용량화되면서 기존에는 보이지 않았던 문제들이 하나둘씩 드러나고 있습니다. 그러나 오늘 소개해드린 GRAID SupremeRAID나 PoseidonOS 등의 새로운 솔루션들이 RAID를 계속하여 발전시킬 수 있다면 앞으로도 RAID는 널리 사용될 것입니다.

---

### 참고

* [https://www.graidtech.com/how-it-works/](https://www.graidtech.com/how-it-works/)
* [https://www.computerweekly.com/news/252526179/GRAID-puts-RAID-on-a-GPU-for-cut-price-disk-protection-and-rebuilds](https://www.computerweekly.com/news/252526179/GRAID-puts-RAID-on-a-GPU-for-cut-price-disk-protection-and-rebuilds)
* [https://blocksandfiles.com/2022/10/12/graids-nuclear-competitive-knockoff/](https://blocksandfiles.com/2022/10/12/graids-nuclear-competitive-knockoff/)
* [https://poseidonos.io/](https://poseidonos.io/)