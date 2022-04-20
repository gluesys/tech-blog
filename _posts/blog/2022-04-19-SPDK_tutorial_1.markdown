---
layout:     post
title:      "SPDK 시리즈 1 : SPDK 환경 구축 실습"
date:       2022-04-19
author:     김 태훈 (thkim@gluesys.com)
categories: blog
tags:       [SPDK, NVMe, SSD, Flash, Memory, RDMA, Storage]
cover:      "/assets/SPDK_maincover.jpg"
main:       "/assets/SPDK_maincover.jpg"
---

인사말
---

최근 스토리지 연구를 수행하면서 SPDK를 다룰 일이 많아졌는데, 관련 자료를 찾다 보니 최신 기술이어서 그런지 실습 정보가 많이 부족하다는 것을 느꼈습니다.

그래서 그동안 경험했던 내용을 잘 정리해서 전달해 보고자 합니다. SPDK 개발에 관심 있으신 분들에게 도움이 되었으면 좋겠습니다.

이번 포스트에서는 NVMe SSD와 SPDK의 최신 코드를 이용해서 테스트 환경을 구축해 보고 SPDK에서 제공하는 스토리지 기능을 실습해 보겠습니다.

시작에 앞서 리눅스 커널의 블록 계층 및 NVMe SSD, SPDK에 대한 지식과 git, 컴파일 경험이 있는 분들은 본 포스트를 이해하는 데 도움이 될 것입니다.

그러면 본격적으로 시작해 보겠습니다!

&nbsp;

SPDK 소개
---

지난 [포스팅](https://tech.gluesys.com/blog/2022/02/18/SPDK_1.html)에서 소개한 바와 같이 SPDK(Storage Performance Development Kit)는 사용자 공간(userspace) 계층에서 NVMe(Non-Volatile Memory Express)와 같은 초고속 SSD 장치를 효율적으로 사용하기 위한 프레임워크입니다.

![Alt text](/assets/SPDK_architecture.jpg) 
<center>그림 1. SPDK Architecture</center>

&nbsp;

SPDK는 크게 스토리지 전용의 인터페이스(Storage Protocol)와 SPDK의 핵심 개념이 정의된 디바이스 드라이버(Driver), 그리고 커널에서 제공하던 블록 장치 기술(Storage Service)로 구성됩니다. SPDK에서는 블록 장치 기술을 'Block Device Driver' 또는 'Block Device Module', 줄여서 'bdev'로 표현합니다.

bdev는 리눅스 커널의 블록 계층과 유사한 기능을 제공하는 C 라이브러리입니다. 블록 계층은 디바이스 드라이버보다 상위 계층이며, 스토리지의 기본 기능들을 제공합니다. 대표적인 기능으로 논리 볼륨과 소프트웨어 RAID, 씬 프로비저닝, 중복 제거 등이 있습니다.
    
SPDK에 구현된 bdev 목록은 다음과 같습니다.
  * Ceph RBD(RADOS Block Device)
  * Thin Provisioning
  * Device Crypto
  * Throughput Delay
  * GPT(for GUID partition table) & Partitioning
  * iSCSI Initiator (binding LUN to bdev)
  * Open CAS Framework(OCF)
  * Malloc(ramdisk)
  * Null(Similar to '/dev/null')
  * NVMe Device
  * Logical Volume
  * Passthrough
  * Pmem
  * S/W RAID
  * Split
  * Uring
  * Virtio-Block & Virtio-SCSI using vhost

익숙한 기능과 처음 보는 기능도 보이네요. 모듈의 자세한 설명은 [링크](https://spdk.io/doc/bdev.html)에서 확인하실 수 있습니다.

이외에도 개발자는 SPDK에서 제공하는 bdev 라이브러리([bdev.h](https://spdk.io/doc/bdev_8h.html))를 이용하여 스토리지 기능을 유저 레벨에서 구현할 수 있습니다.

  * 참고
    - [Presentation of 2018 Storage Developer Conference](https://www.snia.org/sites/default/files/SDC/2018/presentations/SSS_NVM_PM_NVDIMM/Luse_P_Trahe_F_Virtual_BDEVs_The_Secret_to_Customizing_SPDK.pdf)

&nbsp;

# SPDK 환경 구축

이제부터 이번 포스팅의 목표인 SPDK  실습 환경을 구성해 보도록 하겠습니다. 먼저 SPDK 깃허브에서 master 브랜치의 최신 코드를 테스트 장비로 가져옵니다. 

  ```console
  [root@localhost ~]# git clone https://github.com/spdk/spdk
  [root@localhost ~]# cd spdk
  ```

그리고 설치할 코드의 의존성 패키지를 설치합니다.

  ```console
  [root@localhost spdk]# scripts/pkgdep.sh --all
  ```

패키지 설치가 완료되면 빌드를 해줍니다. 이때 컴파일 전에 `./configure` 스크립트를 실행하는데, 어떤 기능들을 활성화 할지 옵션으로 입력해야 합니다. 현재 `./configure`에서 제공되는 옵션 목록은 [링크](https://github.com/spdk/spdk/blob/master/configure#L47)에서 확인할 수 있습니다. 일단은 기본값으로 진행하겠습니다.

  ```console
  [root@localhost spdk]# ./configure
  [root@localhost spdk]# make -j 40
  ```

빌드가 완료되면 시스템의 NVMe SSD를 SPDK 드라이버에서 사용할 수 있도록 시스템과 NVMe SSD의 연결을 해제해야 합니다. 커널은 운영체제가 부팅되면서 컴퓨터에 연결된 장치들을 인식하고 관련된 드라이버를 실행하여 장치를 사용할 수 있도록 준비합니다. 따라서 커널 드라이버에서 장치에 대한 오너쉽을 해제해야 SPDK에서 장치의 오너쉽을 가져올 수 있습니다.

현재 테스트 장비에는 Intel Optane NVMe SSD가 설치되어 있습니다. 해당 장치를 SPDK에서 사용할 수 있도록 준비해 보겠습니다. 커널과의 장치 해제는 `scripts/setup.sh` 스크립트를 사용하면 됩니다.

  ```console
  [root@localhost spdk]# nvme list
  Node             SN                   Model                                    Namespace Usage                      Format           FW Rev
  ---------------- -------------------- ---------------------------------------- --------- -------------------------- ---------------- --------
  /dev/nvme0n1     PHMB7435004J280CGN   INTEL SSDPED1D280GA                      1         280.07  GB / 280.07  GB    512   B +  0 B   E2010325
  [root@localhost spdk]# lsblk | grep nvme
  nvme0n1 259:0    0 260.9G  0 disk
  [root@localhost spdk]# scripts/setup.sh
  0000:80:04.2 (8086 2021): Already using the uio_pci_generic driver
  0000:80:04.3 (8086 2021): Already using the uio_pci_generic driver
  0000:80:04.0 (8086 2021): Already using the uio_pci_generic driver
  0000:80:04.1 (8086 2021): Already using the uio_pci_generic driver
  0000:80:04.6 (8086 2021): Already using the uio_pci_generic driver
  0000:80:04.7 (8086 2021): Already using the uio_pci_generic driver
  0000:80:04.4 (8086 2021): Already using the uio_pci_generic driver
  0000:80:04.5 (8086 2021): Already using the uio_pci_generic driver
  0000:00:04.2 (8086 2021): Already using the uio_pci_generic driver
  0000:00:04.3 (8086 2021): Already using the uio_pci_generic driver
  0000:00:04.0 (8086 2021): Already using the uio_pci_generic driver
  0000:00:04.1 (8086 2021): Already using the uio_pci_generic driver
  0000:00:04.6 (8086 2021): Already using the uio_pci_generic driver
  0000:00:04.7 (8086 2021): Already using the uio_pci_generic driver
  0000:00:04.4 (8086 2021): Already using the uio_pci_generic driver
  0000:00:04.5 (8086 2021): Already using the uio_pci_generic driver
  0000:3b:00.0 (8086 2700): nvme -> uio_pci_generic
  ```

PCIe 0000:3b:00.0 장치에 대한 커널 드라이버 해제가 완료되었습니다. 다시 조회해 볼까요?

  ```console
  [root@localhost spdk]# nvme list
  [root@localhost spdk]# lsblk | grep nvme
  ```

결과가 나오지 않습니다. 관련된 커널 드라이버에서 장치의 오너쉽을 해제했기 때문입니다.

SPDK는 장치의 오너쉽을 사용자 공간의 프로그램에 할당하기 위해 VFIO[^1] 또는 UIO[^2] 기술을 이용합니다. 두 기술에 대한 자세한 설명은 본 포스팅의 목적과 다르니 이 부분은 향후 심화 과정으로 다뤄보겠습니다. 간단한 내용은 [링크](https://spdk.io/doc/concepts.html)를 참고하시면 되겠습니다.

SPDK에서 사용한 장치의 오너쉽을 다시 커널에 넘기려면 `reset` 옵션을 추가하면 됩니다.

  ```console
  [root@localhost spdk]# scripts/setup.sh reset
  0000:3b:00.0 (8086 2700): uio_pci_generic -> nvme
  0000:80:04.2 (8086 2021): uio_pci_generic -> no driver
  0000:80:04.3 (8086 2021): uio_pci_generic -> no driver
  0000:80:04.0 (8086 2021): uio_pci_generic -> no driver
  0000:80:04.1 (8086 2021): uio_pci_generic -> no driver
  0000:80:04.6 (8086 2021): uio_pci_generic -> no driver
  0000:80:04.7 (8086 2021): uio_pci_generic -> no driver
  0000:80:04.4 (8086 2021): uio_pci_generic -> no driver
  0000:80:04.5 (8086 2021): uio_pci_generic -> no driver
  0000:00:04.2 (8086 2021): uio_pci_generic -> no driver
  0000:00:04.3 (8086 2021): uio_pci_generic -> no driver
  0000:00:04.0 (8086 2021): uio_pci_generic -> no driver
  0000:00:04.1 (8086 2021): uio_pci_generic -> no driver
  0000:00:04.6 (8086 2021): uio_pci_generic -> no driver
  0000:00:04.7 (8086 2021): uio_pci_generic -> no driver
  0000:00:04.4 (8086 2021): uio_pci_generic -> no driver
  0000:00:04.5 (8086 2021): uio_pci_generic -> no driver
  [root@localhost spdk]# lsblk | grep nvme
  nvme0n1 259:0    0 260.9G  0 disk
  ```

이어서 SPDK 환경이 정상적으로 구성되었는지 확인해 보겠습니다. 다시 `scripts/setup.sh` 스크립트를 수행하여 테스트할 장치를 준비하고, `build/examples/hello_world` 예제를 수행합니다.

  ```console
  [root@localhost spdk]# build/examples/hello_world
  [2022-01-13 03:44:04.916653] Starting SPDK v22.01-pre git sha1 ed8be4ad0 / DPDK 21.08.0 initialization...
  [2022-01-13 03:44:04.916839] [ DPDK EAL parameters: [2022-01-13 03:44:04.916872] hello_world [2022-01-13 03:44:04.916896] -c 0x1 [2022-01-13 03:44:04.916919] --log-level=lib.eal:6 [2022-01-13 03:44:04.916942] --log-level=lib.cryptodev:5 [2022-01-13 03:44:04.916986] --log-level=user1:6 [2022-01-13 03:44:04.917014] --iova-mode=pa [2022-01-13 03:44:04.917040] --base-virtaddr=0x200000000000 [2022-01-13 03:44:04.917062] --match-allocations [2022-01-13 03:44:04.917086] --file-prefix=spdk0 [2022-01-13 03:44:04.917111] --proc-type=auto [2022-01-13 03:44:04.917133] ]
  EAL: No available 1048576 kB hugepages reported
  EAL: No free 2048 kB hugepages reported on node 1
  TELEMETRY: No legacy callbacks, legacy socket not created
  Initializing NVMe Controllers
  Attaching to 0000:3b:00.0
  Attached to 0000:3b:00.0
  Using controller INTEL SSDPED1D280GA  (PHMB7435004J280CGN  ) with 1 namespaces.
    Namespace ID: 1 size: 280GB
    Initialization complete.
    INFO: using host memory buffer for IO
    Hello world!
  ```

'Hello World!'  개발자라면 익숙한 문장이 보입니다. 예제에서는 커널의 드라이버와 연결 해제한 NVMe 장치를 SPDK에서 직접 통신하여 SSD의 컨트롤러 정보를 불러왔습니다. 예제의 코드는 `examples/nvme/hello_world/hello_world.c`([링크](https://github.com/spdk/spdk/blob/master/examples/nvme/hello_world/hello_world.c))에서 확인할 수 있습니다.

  * 참고
    - https://spdk.io/doc/getting_started.html
    - https://spdk.io/doc/concepts.html
    - https://spdk.io/doc/bdev.html

&nbsp;

# SPDK 실습

SPDK는 bdev와 같은 기능을 동적으로 구성할 수 있도록 JSON-RPC[^3] 프로토콜을 이용하여 프로세스 간의 통신을 수행합니다. 이는 커널에서 시스템 콜을 통해 디바이스 드라이버에 사용자 명령을 전달하는 것과 같은 구조입니다.

`app` 디렉토리에는 SPDK에서 제공하는 모든 구성 요소들을 사용해 보고 테스트할 수 있는 코드가 포함되어 있습니다. 정상적으로 빌드가 완료될 경우 `build/bin` 경로에 프로그램이 생성됩니다. 대표적으로 `spdk_tgt`는 iSCSi target과 NVMe-oF target, Vhost 기능을 모두 제공하는 서버 프로그램입니다. `spdk_tgt`를 실행하면 SPDK 드라이버가 로드되고 SPDK에서 제공하는 모든 구성 요소를 사용할 수 있는 환경이 구성됩니다.

실제 환경에서는 백그라운드 서비스로 구성하겠지만, 본 예제에서는 동작 여부를 확인하기 위해 포그라운드 프로세스로 실행하겠습니다. 별도의 터미널을 띄우고 `build/bin/spdk_tgt`를 실행합니다. 

  * 새로운 터미널에서 수행

  ```console
  [root@localhost spdk]# build/bin/spdk_tgt
  [2022-01-13 03:45:42.140847] Starting SPDK v22.01-pre git sha1 ed8be4ad0 / DPDK 21.08.0 initialization...
  [2022-01-13 03:45:42.141026] [ DPDK EAL parameters: [2022-01-13 03:45:42.141060] spdk_tgt [2022-01-13 03:45:42.141086] --no-shconf [2022-01-13 03:45:42.141108] -c 0x1 [2022-01-13 03:45:42.141142] --log-level=lib.eal:6 [2022-01-13 03:45:42.141189] --log-level=lib.cryptodev:5 [2022-01-13 03:45:42.141217] --log-level=user1:6 [2022-01-13 03:45:42.141241] --iova-mode=pa [2022-01-13 03:45:42.141265] --base-virtaddr=0x200000000000 [2022-01-13 03:45:42.141293] --match-allocations [2022-01-13 03:45:42.141316] --file-prefix=spdk_pid9976 [2022-01-13 03:45:42.141339] ]
  EAL: No available 1048576 kB hugepages reported
  EAL: No free 2048 kB hugepages reported on node 1
  TELEMETRY: No legacy callbacks, legacy socket not created
  [2022-01-13 03:45:42.223467] app.c: 543:spdk_app_start: *NOTICE*: Total cores available: 1
  [2022-01-13 03:45:42.354606] reactor.c: 943:reactor_run: *NOTICE*: Reactor started on core 0
  [2022-01-13 03:45:42.354674] accel_engine.c:1012:spdk_accel_engine_initialize: *NOTICE*: Accel engine initialized to use software engine.
  ```

`spdk_tgt`이 정상적으로 실행되면 RPC 통신을 위한 소켓 파일이 생성됩니다. 다른 터미널에서 소켓이 생성되었는지 확인합니다. 소켓 파일은 `/var/tmp/spdk.sock` 경로에 생성됩니다.

  ```console
  [root@localhost spdk]# ls -l /var/tmp/spdk.sock
  srwxr-xr-x 1 root root 0 Apr  8 19:36 /var/tmp/spdk.sock
  [root@localhost spdk]# lsof -U | grep 'spdk.sock'
  reactor_0  49063           root  373u  unix 0xffff9a31531df2c0      0t0 656974096 /var/tmp/spdk.sock
  [root@localhost spdk]# file /var/tmp/spdk.sock
  /var/tmp/spdk.sock: socket
  ```
자, SPDK 실습을 위한 환경 구성이 완료되었습니다. 이제부터 SPDK에서 제공하는 bdev 중 몇 가지 기능을 사용해 보도록 하겠습니다.

  * 참고
    - https://spdk.io/doc/jsonrpc.html
    - https://spdk.io/doc/app_overview.html
    - https://github.com/spdk/spdk/issues/295

&nbsp;

## NVMe 컨트롤러 등록

 첫 번째 실습은 NVMe SSD의 컨트롤러 정보를 불러오는 방법입니다. 일반적으로 리눅스에서 NVMe SSD를 제어할 때 `nvme` 명령을 사용합니다. `nvme` 명령은 NVMe github의 nvme-cli 코드로 관리되며 NVMe의 최신 스펙에 맞춰서 지속적으로 개발되고 있습니다.
 
 `nvme` 명령으로 NVMe SSD의 다양한 설정을 수행할 수 있습니다. 2019년도 당시, 국제 스토리지 성능 평가를 수행하는 SPC 협회의 SPC-1 성능 테스트를 진행할 때 `nvme` 명령을 사용하여 NVMe SSD의 성능 최적화를 수행했었습니다(~~[당시 세계 성능 5위](https://www.etnews.com/20190102000138), 깨알 자랑~~).
 
 그만큼 `nvme` 명령은 강력한 기능을 제공합니다만, SPDK로 장치의 오너쉽을 넘긴 이상 `nvme` 명령으로는 더 이상 NVMe SSD를 제어할 수 없습니다. 한번 확인해 볼까요?

  ```console
  [root@localhost spdk]# nvme list
  <no output message>
  ```

`nvme` 명령에서 제어할 수 있는 장치가 출력되지 않습니다. 그렇다면 NVMe SSD 컨트롤러 정보를 불러오지 못하는가? 아닙니다. NVMe SSD 제조사는 NVM Express 협회에서 제공하는 표준 스펙을 따라야 합니다.

NVMe 스펙이 공개되기 전까지 PCIe 기반의 SSD는 표준이 없었기 때문에 제조사마다 스펙이 제각각 이였고, 대부분의 기술이 공개되지 않아 소프트웨어 계층에서는 적극적인 활용이 어려웠습니다. 이러한 문제에 직면하여 여러 진영에서 표준화 작업을 진행하였고, 2013년 인텔이 주도한 PCIe SSD 협회에서 표준 스펙인 NVM Express 1.0e 버전을 공개했습니다.
    
음... 잠깐 샛길로 빠졌군요. 다시 돌아와서! NVMe 스펙을 참고하여 SPDK에서도 `nvme` 명령과 유사한 작업을 수행할 수 있습니다. `spdk_tgt`을 포그라운드 프로세스로 실행한 상태에서 다른 터미널로 접속하여 설치되어 있는 NVMe SSD의 PCIe 번호를 확인합니다.

  ```console
  [root@localhost spdk]# lspci | grep -i ssd
  3b:00.0 Non-Volatile memory controller: Intel Corporation Optane SSD 900P Series
  ```

아 좋습니다. 인텔의 Optane SSD 900P 시리즈 제품이 확인되네요. 쪼금 자랑하면 연구소에는 이런 제품이 사무용 마우스보다 훨씬 많습니다(현재 120만 원, 출시 당시 가격 ㅎㄷㄷ).

`3b:00.0`을 확인했으니 컨트롤러를 SPDK에 연결해 봅니다. 이때, RPC 통신을 위해서 모든 명령은 `scripts/rpc.py`로 수행되어야 합니다. 실행할 명령은 `bdev_nvme_attach_controller`입니다. 연결할 컨트롤러의 이름은 `NVMe0`, 연결 방식은 `pcie`로 하겠습니다.

  ```console
  [root@localhost spdk]# scripts/rpc.py bdev_nvme_attach_controller -b NVMe0 -t pcie -a 0000:3b:00.0
  NVMe0n1
  ```

오 뭔가 명령이 잘 수행된 느낌입니다. 다음으로 `bdev_nvme_get_controllers` 명령을 수행하여 연결된 컨트롤러 정보를 불러오겠습니다.

  ```console
  [root@localhost spdk]# scripts/rpc.py bdev_nvme_get_controllers
  [
    {
      "name": "NVMe0",
      "trid": {
        "trtype": "PCIe",
        "traddr": "0000:3b:00.0"
      },
      "host": {
        "nqn": "nqn.2014-08.org.nvmexpress:uuid:2b4d86b5-b34a-4983-9830-2978727acb4a",
        "addr": "",
        "svcid": ""
      }
    }
  ]
  ```

:clap: :clap: :clap: 연결된 컨트롤러 정보를 확인할 수 있습니다. 반대로 연결 해제는 `bdev_nvme_detach_controlle` 명령을 사용합니다.

  ```console
  [root@localhost spdk]# scripts/rpc.py bdev_nvme_detach_controller NVMe0
  [root@localhost spdk]# scripts/rpc.py bdev_nvme_get_controllers
  []
  ```

이외에도 SPDK는 nvme와 관련된 다양한 기능을 제공합니다.

  ```console
  [root@localhost spdk]# scripts/rpc.py | grep nvme
      bdev_nvme_set_options (set_bdev_nvme_options)
                            Set options for the bdev nvme type. This is startup
      bdev_nvme_set_hotplug (set_bdev_nvme_hotplug)
                            Set hotplug options for bdev nvme type.
      bdev_nvme_attach_controller (construct_nvme_bdev)
                            Add bdevs with nvme backend
      bdev_nvme_get_controllers (get_nvme_controllers)
      bdev_nvme_detach_controller (delete_nvme_controller)
      bdev_nvme_reset_controller
      bdev_nvme_cuse_register
      bdev_nvme_cuse_unregister
      bdev_nvme_apply_firmware (apply_firmware)
      bdev_nvme_get_transport_statistics
                            Get bdev_nvme poll group transport statistics
      bdev_nvme_get_controller_health_info
      bdev_nvme_opal_init
      bdev_nvme_opal_revert
      bdev_nvme_send_cmd (send_nvme_cmd)
  ```

NVMe SSD 최적화를 위해 제조사에서 제공하는 컨트롤러 설정을 변경하고 싶다!? ~~힘들지만~~ 방법은 있습니다.

먼저 PCIe configuration register format(아래 그림 2)을 보시고, BAR(Base Address Registers)에 등록된 NVMe controller register format(아래 그림 3)을 확인한 다음에, 얻으려는 정보가 매핑된 메모리의 위치를 찾아서 `bdev_nvme_send_cmd` 명령을 사용해서 NVMe 컨트롤러에 명령을 보내면 알려줍니다.

![Alt text](/assets/pci_header.png)
<center>그림 2. PCIe configuration register format</center>

&nbsp;

![Alt text](/assets/nvme_register.png)
<center>그림 3. NVMe controller register format</center> 

&nbsp;

점점 깊어지고 실습하기 싫어지네요. 하드웨어를 잘 아는 개발자들이 NVMe 스펙을 참고해서 일반인도 편히 사용할 수 있는 `nvme` 명령을 만들었는데, 그걸 사용하지 못하니까 답답합니다.

다행히도 SPDK에서는 `nvme` 명령처럼 기존 프로그램에서 NVMe SSD와 직접 통신할 수 있는 방법을 제공합니다. 바로 문자 드라이버 등록입니다.

  * 참고
    - 그림 출처 : [NVMe Spec. version 1.4b document](https://nvmexpress.org/wp-content/uploads/NVM-Express-1_4b-2020.09.21-Ratified.pdf)

&nbsp;

## 문자 드라이버 등록

우리가 컴퓨터에 장치를 연결하면 리눅스 커널은 장치를 인식해서 알맞은 드라이버를 호출합니다. 리눅스에서 관리하는 디바이스 드라이버는 문자, 블록, 네트워크로 구분됩니다. 이 중에서 문자 드라이버는 장치를 파일로 추상화하며, 스트림 방식의 데이터 전송을 수행합니다.

시스템 콜[^4] ioctl()은 스트림 방식으로 장치를 제어할 수 있는 대표적인 기능입니다. `nvme` 명령도 대부분 ioctl()를 통해 장치를 제어합니다. 하지만, SPDK에 장치를 등록하면 커널에서 사용할 수 없기 때문에 일반적인 방법으로 다룰 수 없습니다. 이를 위해 SPDK는 CUSE[^5] 라이브러리를 이용하여 사용자 공간에서 구현된 SPDK 기능을 문자 드라이버로 제공합니다.

이제 문자 드라이버 등록 실습을 해보겠습니다. 먼저 테스트 서버에 cuse 패키지를 설치해야 합니다. 동작 중인 `spdk_tgt`를 Ctrl+C로 종료하고, ./configure 명령에 `--with-nvme-cuse` 옵션을 추가하고 리빌드를 수행합니다.

  ```console
  [2022-01-13 03:46:48.864407] bdev_nvme_rpc.c: 400:rpc_bdev_nvme_attach_controller: *ERROR*: The multipath parameter was not specified to bdev_nvme_attach_controller but it was used to add a failover path. This behavior will default to rejecting the request in the future. Specify the 'multipath' parameter to control the behavior[2022-01-13 03:46:33.714712] bdev_nvme.c:3620:bdev_nvme_delete: *ERROR*: Failed to find NVMe bdev controller
  ^C
  [root@localhost spdk]# 
  [root@localhost spdk]# ./configure --with-nvme-cuse
  Notice: ISA-L, compression & crypto require NASM version 2.14 or newer. Turning off default ISA-L and crypto features.
  Using default SPDK env in /root/spdk/lib/env_dpdk
  Using default DPDK in /root/spdk/dpdk/build
  Creating mk/config.mk...done.
  Creating mk/cc.flags.mk...done.
  Type 'make' to build.
  [root@localhost spdk]# make -j 40
  ... <Done>
  ```

리빌드가 완료되었습니다. `spdk_tgt` 프로그램을 실행하기 전에 cuse 커널 모듈을 불러옵니다.

  ```console
  [root@localhost spdk]# modprobe cuse
  [root@localhost spdk]# lsmod | grep cuse
  cuse                   13274  0
  fuse                  100350  4 cuse
  [root@localhost spdk]# ./build/bin/spdk_tgt
  [2022-01-13 03:47:44.436670] Starting SPDK v22.01-pre git sha1 ed8be4ad0 / DPDK 21.08.0 initialization...
  [2022-01-13 03:47:44.436857] [ DPDK EAL parameters: [2022-01-13 03:47:44.436891] spdk_tgt [2022-01-13 03:47:44.436919] --no-shconf [2022-01-13 03:47:44.436945] -c 0x1 [2022-01-13 03:47:44.436969] --log-level=lib.eal:6 [2022-01-13 03:47:44.436995] --log-level=lib.cryptodev:5 [2022-01-13 03:47:44.437019] --log-level=user1:6 [2022-01-13 03:47:44.437072] --iova-mode=pa [2022-01-13 03:47:44.437098] --base-virtaddr=0x200000000000 [2022-01-13 03:47:44.437121] --match-allocations [2022-01-13 03:47:44.437145] --file-prefix=spdk_pid66198 [2022-01-13 03:47:44.437168] ]
  EAL: No available 1048576 kB hugepages reported
  EAL: No free 2048 kB hugepages reported on node 1
  TELEMETRY: No legacy callbacks, legacy socket not created
  [2022-01-13 03:47:44.519003] app.c: 543:spdk_app_start: *NOTICE*: Total cores available: 1
  [2022-01-13 03:47:44.648331] reactor.c: 943:reactor_run: *NOTICE*: Reactor started on core 0
  [2022-01-13 03:47:44.648394] accel_engine.c:1012:spdk_accel_engine_initialize: *NOTICE*: Accel engine initialized to use software engine.
  ```

리빌드 및 `spdk_tgt`이 정상적으로 실행되었다면 다른 터미널에서 문자 드라이버를 등록해 보겠습니다. 문자 드라이버 등록은 `bdev_nvme_cuse_register` 명령으로 수행합니다.

  ```console
  [root@localhost spdk]# scripts/rpc.py bdev_nvme_attach_controller -b NVMe0 -t PCIe -a 0000:3b:00.0
  NVMe0n1
  [root@localhost spdk]# scripts/rpc.py bdev_nvme_cuse_register -n NVMe0
  ```

`spdk_tgt` 터미널에서 문자 드라이버가 정상적으로 생성되었다는 로그가 출력됩니다.

  ```console
  [2022-01-13 03:47:52.183893] nvme_cuse.c: 972:nvme_cuse_start: *NOTICE*: Creating cuse device for controller
  [2022-01-13 03:47:52.184053] nvme_cuse.c: 763:cuse_session_create: *NOTICE*: fuse session for device spdk/nvme0 created
  [2022-01-13 03:47:52.184117] nvme_cuse.c: 763:cuse_session_create: *NOTICE*: fuse session for device spdk/nvme0n1 created
  ```

다른 터미널에서 문자 드라이버가 생성되었는지 확인해 보겠습니다. `/dev/spdk` 디렉토리 하위에 위치합니다.

  ```console
  [root@localhost spdk]# ls /dev/spdk/
  nvme0  nvme0n1
  ```

이제 `nvme` 명령을 사용해서 컨트롤러 정보를 확인해 봅시다. `nvme id-ctrl` 명령에 `-H` 옵션(--human-readable)을 추가하면 [그림 3]에서 보여준 NVMe controller register format 정보를 보기 쉽게 변환해 줍니다.

  ```console
  [root@localhost spdk]# nvme id-ctrl /dev/spdk/nvme0 -H
  NVME Identify Controller:
  vid       : 0x8086
  ssvid     : 0x8086
  sn        : PHMB7435004J280CGN
  mn        : INTEL SSDPED1D280GA
  fr        : E2010325
  rab       : 0
  ieee      : 5cd2e4
  cmic      : 0
  [2:2] : 0     PCI
  [1:1] : 0     Single Controller
  [0:0] : 0     Single Port
  ...
  [root@localhost spdk]# scripts/rpc.py bdev_get_bdevs
  [
    {
    "name": "NVMe0n1",
      "aliases": [],
      "product_name": "NVMe disk",
      "block_size": 512,
      "num_blocks": 547002288,
      "uuid": "0b1f1ff5-4bb6-4fea-b436-0359ad12f7ee",
      "assigned_rate_limits": {
        "rw_ios_per_sec": 0,
        "rw_mbytes_per_sec": 0,
        "r_mbytes_per_sec": 0,
        "w_mbytes_per_sec": 0
      },
      "claimed": true,
      "zoned": false,
      "supported_io_types": {
        "read": true,
        "write": true,
        "unmap": true,
        "write_zeroes": true,
        "flush": true,
        "reset": true,
        "nvme_admin": true,
        "nvme_io": true
      },
      "driver_specific": {
        "nvme": {
          "pci_address": "0000:3b:00.0",
          "trid": {
            "trtype": "PCIe",
            "traddr": "0000:3b:00.0"
          },
          "cuse_device": "spdk/nvme0n1",
          "ctrlr_data": {
            "vendor_id": "0x8086",
            "model_number": "INTEL SSDPED1D280GA",
            "serial_number": "PHMB7435004J280CGN",
            "firmware_revision": "E2010325",
            "oacs": {
              "security": 1,
              "format": 1,
              "firmware": 1,
              "ns_manage": 0
            }
          },
          "vs": {
            "nvme_version": "1.0"
          },
          "ns_data": {
            "id": 1
          },
          "security": {
            "opal": false
          }
        }
      }
    }
  ]
  ```

`nvme id-ctrl`로 확인한 NVMe SSD 정보와 SPDK의 `bdev_get_bdevs` 출력 결과가 동일한 것을 확인할 수 있습니다.
마지막으로 문자 드라이버 등록을 해제하려면 `bdev_nvme_cuse_unregister` 명령을 사용하면 됩니다.

  ```console
  [root@localhost spdk]# scripts/rpc.py bdev_nvme_cuse_unregister -n NVMe0
  [root@localhost spdk]# ls /dev/spdk/nvme0
  ls: cannot access /dev/spdk/nvme0: No such file or directory
  ```

  * 참고
    - https://spdk.io/doc/nvme.html

&nbsp;

## lvol 생성

다음으로 논리 볼륨을 생성해 보겠습니다. SPDK에서는 lvol 모듈을 통해 논리 볼륨을 구성할 수 있습니다. lvol은 리눅스 커널에서 제공하는 LVM(Logical Volume Manager)[^6]의 LV(Logical Volume)과 유사한 기능입니다.

lvol 생성은 NVMe SSD를 '논리 볼륨 저장소'에 등록하는 작업이 선행되어야 합니다. 이는 LVM에서 PV(Physical Volume)를 VG(Volume Group)에 등록하는 작업과 유사합니다. 논리 볼륨 저장소는 lvstore로 불립니다. lvstore 생성은 `bdev_lvol_create_lvstore` 명령을 사용합니다. `bdev_lvol_create_lvstore`의 첫 번째 인자는 `bdev_get_bdevs` 명령으로 출력된 장치의 이름이 입력되며, 두 번째 인자는 등록할 신규 논리 볼륨 저장소의 이름입니다.

  ```console
  [root@localhost spdk]# scripts/rpc.py bdev_lvol_create_lvstore NVMe0n1 lvs
  1818d45a-3a05-42c9-bbb2-9229cc25ac49
  ```

NVMe SSD가 논리 볼륨 저장소에 정상적으로 등록되면 생성된 lvstore의 uuid를 출력합니다. 논리 볼륨 저장소는 `bdev_lvol_get_lvstores` 명령으로 확인할 수 있지만, `bdev_get_bdevs` 명령으로는 확인할 수 없습니다.

  ```console
  [root@localhost spdk]# scripts/rpc.py bdev_lvol_get_lvstores
  [
    {
      "uuid": "1818d45a-3a05-42c9-bbb2-9229cc25ac49",
        "name": "lvs",
        "base_bdev": "NVMe0n1",
        "total_data_clusters": 66706,
        "free_clusters": 66706,
        "block_size": 512,
        "cluster_size": 4194304
    }
  ]
  ```

논리 볼륨 저장소 삭제는 `bdev_lvol_delete_lvstore` 명령을 사용합니다.

  ```console
  [root@localhost spdk]# scripts/rpc.py bdev_lvol_delete_lvstore -l lvs
  [root@localhost spdk]# scripts/rpc.py bdev_lvol_get_lvstores
  []
  ```

다음으로 논리 볼륨을 생성해 보겠습니다. 논리 볼륨은 `bdev_lvol_create` 명령으로 생성할 수 있습니다. `bdev_lvol_create`의 첫 번째 인자는 생성할 논리 볼륨의 이름이며, 두 번째 인자는 논리 볼륨의 크기로 기본 단위는 MiB입니다. 마지막으로 `-l` 옵션으로 생성된 논리 볼륨 저장소의 이름 또는 uuid를 입력합니다. 예제로 lvs 이름의 논리 볼륨 저장소에 1GB 용량을 갖는 lvol1 논리 볼륨을 생성해 보겠습니다.

  ```console
  [root@localhost spdk]# scripts/rpc.py bdev_lvol_create lvol1 1024 -l lvs
  68ba7bbc-d26b-464b-ae12-f48a62512b0d
  ```

논리 볼륨이 정상적으로 생성되면 논리 볼륨 저장소와 마찬가지로 lvol의 uuid를 출력합니다. SPDK에서 생성된 논리 볼륨은 `bdev_get_bdevs` 명령으로 확인할 수 있지만, `bdev_get_lvstores`와 같이 논리 볼륨 정보만 출력하는 명령은 제공하지 않습니다.

  ```console
  [root@localhost spdk]# scripts/rpc.py bdev_get_bdevs
  [
    {...},
    {
        "name": "68ba7bbc-d26b-464b-ae12-f48a62512b0d",
        "aliases": [
            "lvs/lvol1"
        ],
        "product_name": "Logical Volume",
        "block_size": 512,
        "num_blocks": 2097152,
        "uuid": "68ba7bbc-d26b-464b-ae12-f48a62512b0d",
        "assigned_rate_limits": {
            "rw_ios_per_sec": 0,
            "rw_mbytes_per_sec": 0,
            "r_mbytes_per_sec": 0,
            "w_mbytes_per_sec": 0
        },
        "claimed": false,
        "zoned": false,
        "supported_io_types": {
            "read": true,
            "write": true,
            "unmap": true,
            "write_zeroes": true,
            "flush": false,
            "reset": true,
            "nvme_admin": false,
            "nvme_io": false
        },
        "driver_specific": {
            "lvol": {
                "lvol_store_uuid": "6579330a-4748-472c-a249-adce070ec15e",
                "base_bdev": "NVMe0n1",
                "thin_provision": false,
                "snapshot": false,
                "clone": false
            }
        }
    }
  ]
  ```

`bdev_get_bdevs` 수행 결과, 논리 볼륨 저장소 lvs에서 1GB 용량을 갖는 논리 볼륨 lovl1이 생성된 것을 확인할 수 있습니다. 이때 볼륨의 용량은 `block_size`와 `num_blocks` 값으로 계산할 수 있습니다. 위 예시에서는 512 byte 크기를 갖는 블록이 2,097,152개 생성되어 전체 1,073,741,824 byte(=1GB) 용량이 할당되었음을 확인할 수 있습니다.

생성된 논리 볼륨 삭제는 `bdev_lvol_delete` 명령을 사용합니다.

  ```console
  [root@localhost spdk]# scripts/rpc.py bdev_lvol_delete lvs/lvol1
  ```

이외에도 논리 볼륨은 스냅샷, 클론, 크기 변경 등, 다양한 기능들 제공합니다. 추가 기능에 대한 설명은 [logical volumes document](https://spdk.io/doc/logical_volumes.html)에서 확인할 수 있습니다.

  * 참고
    - https://spdk.io/doc/bdev.html
    - https://spdk.io/doc/logical_volumes.html

&nbsp;

## RAID 생성

SPDK는 소프트웨어 기반의 RAID[^7] 볼륨을 지원합니다. 다만 현재까지 공식적으로 제공하는 기능은 레벨 0 뿐입니다. RAID-0은 RAID 볼륨에 참여한 장치에 데이터가 분산되는 구조로, 성능은 뛰어나지만 하나의 장치에 이상이 생길 경우 데이터의 무결성이 깨질 수 있습니다.

대부분의 소프트웨어 RAID는 RAID 볼륨 정보(metdata)를 볼륨에 포함된 장치의 특정 영역에 직접 기록하지만, SPDK의 RAID는 저장매체에 RAID 볼륨 정보를 기록하지 않습니다. 이 경우 SPDK 프레임워크를 재시작하면 기존에 구성했었던 RAID 정보를 불러올 수 없어 주의가 필요합니다. (※RAID와 반대로 논리 볼륨은 재시작을 하더라도 구성 정보를 불러옵니다.)

RAID 볼륨은 `bdev_raid_create` 명령으로 생성할 수 있습니다. 이때 생성할 RAID 이름(`-n`)과 스트라이프 크기(`-z`), RAID 번호(`-r`), 등록할 장치(`-b`)를 입력해야 합니다. 예제로 4개의 lvol를 묶어서 레벨 0 RAID 볼륨을 생성해 보겠습니다.

  ```console
  [root@localhost spdk]# scripts/rpc.py bdev_raid_create -n raid0 -z 64 -r 0 -b "lvol1 lvol2 lvol3 lvol4"
  ```

아무런 결과가 출력되지 않았다면 정상적으로 생성되었다는 뜻입니다(?).

RAID 장치 정보는 `bdev_raid_get_bdevs` 명령을 통해 확인할 수 있는데, 이때 인자 값으로 RAID의 상태 카테고리를 입력해야 합니다. 카테고리는 `all`, `online`, `configuring`, `offline`이 있습니다.

  ```console
  [root@localhost spdk]# scripts/rpc.py bdev_raid_get_bdevs all
  raid0
  ```

아쉽게도 RAID에 대한 정보를 확인하는 명령은 제공되지 않습니다. 현재 구현된 RAID 관련된 기능은 생성, 리스트 출력, 삭제 기능뿐입니다. `bdev_get_bdevs` 결과에서도 구성한 RAID 정보는 확인할 수 없습니다.

삭제는 `bdev_raid_delete` 명령을 통해 수행합니다.

  ```console
  [root@localhost spdk]# scripts/rpc.py bdev_raid_delete raid0
  ```

RAID 생성과 마찬가지로 정상적으로 삭제된 경우 아무 결과를 출력하지 않습니다(???).

RAID bdev 모듈은 아직까지 다양한 기능을 지원하지 않습니다. 따라서 현재까지 구현된 기능만으로는 높은 성능이 요구되지만 안정성은 낮아도 괜찮은 일회성 저장 목적으로 사용할 수 있겠습니다.

다만 RAID에 대한 추가 기능 제공이 전혀 없는 것은 아닌 것 같습니다. 커뮤니티에서는 RAID-5 구현에 대한 필요성이 언급되었으며([링크](https://lists.01.org/hyperkitty/list/spdk@lists.01.org/thread/DBSZDNBGNWV6PD7MOF7V5M7EOQP4EVTJ/)), RAID-1의 경우 일부 코드가 [yupeng0921 github](https://github.com/yupeng0921/spdk/tree/raid1/module/bdev/raid1)에 공개되어 있습니다. 또한 SPDK github에는 [RAID-5 코드](https://github.com/spdk/spdk/blob/master/module/bdev/raid/raid5.c)를 일부 확인할 수 있습니다.

아하, 그렇다면 가까운 미래에 안정적으로 레벨 5 RAID 볼륨을 사용할 수 있을 것으로 생각하고 현재 버전에서 RAID-5 볼륨을 생성하는 방법을 실습해 보겠습니다.

먼저 `./configure`에서 `--with-raid5` 옵션을 추가하고 리빌드를 수행해야 합니다. 

  ```console
  [root@localhost spdk]# ./configure --with-raid5
  [root@localhost spdk]# make -j 40
  [root@localhost spdk]# ./build/bin/spdk_tgt
  ```

리빌드 및 `spdk_tgt` 시작을 완료하고 `bdev_raid_create` 명령에서 RAID 레벨(`-r`)을 5로 입력하면 RAID-5 볼륨을 생성할 수 있습니다. 하지만 RAID-0과 마찬가지로 재시작 시 구성했던 볼륨 정보는 사라집니다.

  ```console
  [root@localhost spdk]# scripts/rpc.py bdev_raid_create -n raid5 -z 64 -r 5 -b "lvol1 lvol2 lvol3 lvol4"
  [root@localhost spdk]# scripts/rpc.py bdev_raid_get_bdevs all
  raid5
  ```

  * 참고
    - https://lists.01.org/hyperkitty/list/spdk@lists.01.org/thread/DBSZDNBGNWV6PD7MOF7V5M7EOQP4EVTJ/
    - https://github.com/yupeng0921/spdk/tree/raid1/module/bdev/raid1
    - https://github.com/spdk/spdk/blob/master/module/bdev/raid/raid5.c

&nbsp;

마치며
-----

이번 포스팅에서는 NVMe SSD가 설치된 실장비에 SPDK 최신 코드를 올려보고 bdev 모듈에서 제공하는 일부 기능을 사용해 보았습니다. 다음 시간에는 SPDK 성능 리포트를 분석하고 SPDK 환경에서 성능을 측정해 보겠습니다. 그럼 다음에 만나요 :wave:

&nbsp;

각주
---

[^1]: VFIO : [Virtual Function I/O](https://www.kernel.org/doc/Documentation/vfio.txt)
[^2]: UIO : [Userspace I/O](https://www.kernel.org/doc/html/v4.12/driver-api/uio-howto.html)
[^3]: JSON-RPC : https://www.jsonrpc.org/specification
[^4]: System-call : https://en.wikipedia.org/wiki/System_call
[^5]: CUSE : [Character device in Userspace](https://lwn.net/Articles/308445/)
[^6]: LVM : [Logical Volume Manager](https://en.wikipedia.org/wiki/Logical_Volume_Manager_(Linux))
[^7]: RAID : [Redundant Array of Inexpensive Disks](https://en.wikipedia.org/wiki/RAID)
