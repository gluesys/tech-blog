---
layout:     post
title:      "Lustre File System과 GPU Direct Storage 소개"
date:       2022-06-30
author:     권세훈 (qsh700@gluesys.com)
categories: blog
tags:       [Lustre, HPC, RDMA, Storage, GPU Direct Storage]
cover:      "/assets/lustre_maincover.jpg"
main:       "/assets/lustre_maincover.jpg"
---

# Lustre File System 소개

High Performance Computing(HPC) 클러스터는 대규모 애플리케이션에 최고의 컴퓨팅 성능을 제공하기 위해 사용됩니다. `HPC` 클러스터에서는 많은 양의 데이터를 처리합니다. 꽤 오랜 시간 동안 프로세서와 메모리의 속도는 급격히 증가했지만 I/O 시스템의 성능은 이보다 뒤처지고 있습니다. 따라서 상대적으로 성능이 떨어지는 I/O 성능은 클러스터의 전체 성능을 저하 시킬 수 있습니다. 이를 위해  `lustre File System`을 사용합니다.
 
`러스터(Lustre)`는 병렬 분산 파일 시스템으로 주로 고성능 컴퓨팅의 대용량 파일 시스템으로 사용되고 있습니다. 
`러스터(Lustre)`의 이름은 `Linux`와 `Cluster`의 혼성어에서 유래됐습니다. 

러스터는 `GNU GPL` 정책의 일환으로 개방되어 있으며 소규모 클러스터 시스템부터 대규모 클러스터 시스템용 고성능 파일 시스템입니다. 

러스터는 `Linux` 기반 운영체제에서 실행되며 클라이언트(Client)-서버(Server) 네트워크 아키텍처를 사용합니다.

&nbsp;

# Lustre FS Architecture
![Lustre FS Architecture](/assets/Lustre_Architecture.PNG)
<center>그림 1. Lustre Architecture </center>

&nbsp;

* MGS(Management Server)
  * 모든 러스터 파일 시스템에 대한 구성 정보를 클러스터에 저장하고 이 정보를 다른 `Lustre` 호스트에 제공합니다.

* MGT(Management Target)
  * 모든 러스터 노드에 대한 구성 정보는 `MGS`에 의해 `MGT`라는 저장 장치에 기록됩니다.

* MDS(Metadata Server)
  * 러스터 파일 시스템의 모든 네임 스페이스를 제공하여 파일 시스템의 `아이노드(inodes)`를 저장합니다. 
  * 파일 열기 및 닫기, 파일 삭제 및 이름 변경, 네임 스페이스 조작 관리를 합니다. 
  * 러스터 파일 시스템에서는 하나 이상의 `MDS`와 `MDT`가 존재합니다.

* MDT(Metadata Target)
  * `MDS`의 메타 데이터 정보를 지속적으로 유지하는데 사용되는 저장 장치입니다.

* OSS(Object Storage Servers)
  * 하나 이상의 로컬 `OST`에 대한 파일 I/O 서비스 및 네트워크 요청 처리를 제공합니다. 

* OST(Object Storage Target)
  * `OSS` 호스트에 고르게 분산되어 성능의 균형을 유지하고 처리량을 최대화합니다.

* Lustre clients
  * 각 `클라이언트(client)`는 여러 다른 러스터 파일 시스템 인스턴스를 동시에 마운트 가능합니다.

* LNet(Lustre Networking)
  * 클라이언트가 파일 시스템에 액세스하는데 사용하는 고속 데이터 네트워크 프로토콜입니다.

&nbsp;

# Lustre FS 특징 및 기능
&nbsp;

## HSM(Hierarchical Storage Management)

`HSM`은 고가의 저장매체와 저가의 저장매체 간의 데이터를 자동으로 이동하는 데이터 저장 기술입니다.

`HSM`을 사용하면 다음과 같은 이점이 있습니다. 회사에서는 새 장비에 투자하지 않고도 이미 보유하고 있는 리소스를 최대한 활용할 수 있습니다. 또한, 가장 중요한 데이터의 운선 순위를 저장하여 고속 저장 장치의 공간을 확보합니다. 고속 저장 장치 보다 저속 저장 장치의 비용이 훨씬 저렴하기 때문에 스토리지 비용을 절감할 수 있습니다. 이는 기업에서 비용이 증가할 수 있는 대량의 데이터를 관리하는 경우에 특히 경제적입니다.

* HSM Architecture

![HSM](/assets/HSM_Architecture.png)
<center>그림 2. HSM Architecture </center>

&nbsp;

  * 러스터 파일 시스템을 하나 이상의 외부 스토리지 시스템에 연결할 수 있습니다.
  * 파일을 읽기, 쓰기, 수정과 같이 파일에 접근하게 되면 `HSM` 스토리지에서 러스터 파일 시스템으로 파일을 다시 가져옵니다.
  * 파일을 `HSM` 스토리지에 복사하는 프로세스를 `아카이브(Archive)`라고 하고 아카이브가 완료되면 러스터 파일 시스템에 존재하는 데이터를 삭제할 수 있습니다. 이것을 `Release`라고 말합니다. `HSM`스토리지에서 러스터 파일 시스템으로 데이터를 반환하는 프로세스를 `restore`라 하고 여기서 말하는 restore와 archive는 `HSM Agent`라는 데몬이 필요합니다.
  * `에이전트(Agent)`는 `coopytool`이라는 유저 프로세스가 실행되어 러스터 파일 시스템과 `HSM`간의 파일 아카이브 및 복원을 관리합니다.
  * `코디네이터(Coordinator)`는 러스터 파일 시스템을 `HSM` 시스템에 바인딩하려면 각 파일 시스템 `MDT`에서 코디네이터가 활성화되어야 합니다.

* HSM과 러스터 파일 시스템간의 데이터 관리 유형은 5가지의 요청으로 이루어집니다.
  * archive : 러스터 파일 시스템 파일에서 `HSM` 솔루션으로 데이터를 복사합니다.
  * release : 러스터 파일 시스템에서 파일 데이터를 제거합니다.
  * restore : `HSM` 솔루션에서 해당 러스터 파일 시스템으로 파일 데이터를 다시 복사합니다.
  * remove : `HSM` 솔루션에서 데이터 사본을 삭제합니다.
  * cancel : 진행 중이거나 보류 중인 요청을 삭제합니다.

&nbsp;

## PCC(Persistent Client Cache)

![pcc](/assets/PCC_Architecture.png)
<center>그림 3. Persistent Client Cache </center>

&nbsp;

`PCC`는 러스터 클라이언트 측에서 로컬 캐시 그룹을 제공하는 프레임워크입니다. 각 클라이언트는 `OST`대신 로컬 저장 장치를 자체 캐시로 사용합니다. 로컬 파일 시스템은 로컬 저장장치 안에 있는 캐시 데이터를 관리하는 데 사용됩니다. 캐시 된 I/O의 경우 로컬 파일 시스템으로 전달되어 처리되고 일반 I/O는 OST로 전달됩니다.

`PCC`는 데이터 동기화를 위해 `HSM` 기술을 사용합니다. `HSM copytool`을 사용하여 로컬 캐시에서 `OST`로 파일을 복원합니다. 각 `PCC`에는 고유한 아카이브 번호로 실행되는 copytool 인스턴스가 있고 다른 러스터 클라이언트에서 접근하게 되면 데이터 동기화가 진행됩니다. `PCC`가 있는 클라이언트가 오프라인 될 시 캐시 된 데이터는 일시적으로 다른 클라이언트에서 접근할 수 없게 됩니다. 이후 `PCC` 클라이언트가 재부팅되고 `copytool`이 다시 동작하면 캐시 데이터에 다시 접근할 수 있습니다.

* PCC 이점
 
클라이언트에서 로컬 저장장치를 캐시로 이용하게 되면 네트워크 지연이 없고 다른 클라이언트에 대한 오버헤드가 없습니다. 또한, 로컬 저장장치를 I/O 속도가 빠른 `SSD` or `NVMe SSD`를 통해 좋은 성능을 낼 수 있습니다. `SSD`는 모든 종류의 `SSD`가 사용가능하며, 캐시 장치로 이용할 수 있습니다. `PCC`를 통해 작거나 임의의 I/O를 `OST`로 저장할 필요 없이 로컬 캐시 장치에 저장하여 사용하면 `OST`용량의 부담을 줄일 수 있는 장점이 있습니다.

&nbsp;

## OverStriping

![Overstriping Example](/assets/overstriping.PNG)
<center>그림 4. Overstriping Example</center>

&nbsp;

오버스트라이핑(overstriping)은 기존에 `OST`당 하나였던 `stripe`를 여러 개의 `stripe`를 가질 수 있게 만든 것입니다. 기본적으로 스트라이프의 크기는 1M(1048576byte)로 되어있습니다.

일반적으로 러스터에서는 스트라이프를 구성하기 전 순차적으로 `OST`에 저장되는 것을 확인할 수 있습니다. `stripe`를 구성 후에는 각 `OST`마다 동등하게 분배되어 파일이 저장되는 것을 확인할 수 있습니다. 오버스트라이핑 같은 경우 아래 [그림 5]에서 볼 수 있듯이 일반 스트라이핑으로 구성한 것보다 빠르다는 장점이 있습니다.

다음은 일반 스트라이핑 구성과 오버스트라이핑을 구성하는 명령어입니다.
```console
//Client에서 실행
[root@lzfs-client ~]# lfs setstripe --stripe-count 4 [file or directory name] //OST가 4개일 때 4개의 스트라이프
[root@lzfs-client ~]# lfs setstripe --overstripe-count 8 [file or directory name] //OST가 4개일 때 8개의 스트라이프

//stripe 구성 확인
[root@lzfs-client ~]# lfs getstripe [file or directory name]
```
* Overstriping 이점

![Overstriping Performance](/assets/overstriping2.PNG)
<center>그림 5. overstriping Performance</center>

&nbsp;

## DOM(Data-On-MDT)

`lustre FS`는 현재 대용량 파일에 최적화되어 있습니다. 이로 인해 파일 크기가 너무 작은 단일 파일일 경우 성능이 크게 저하되는 문제가 있습니다. `DoM`은 작은 파일을 `MDT`에 저장하여 이러한 문제를 해결합니다. `DoM`을 이용해서 `MDT`에 작은 파일을 저장하였을 때 추가적으로 `OST`에 접근할 필요가 없어 작은 I/O에 대한 성능이 향상됩니다.

`DoM`은 두 가지 구성요소가 있습니다. 첫 번째는 `MDT` 컴포넌트 두 번째는 `OST stripe`로 구성됩니다. 기본적으로 `DoM`의 `MDT stripe` 크기는 1M로 설정되어있습니다. 이를 변경하기 위해서는 다음과 같은 명령어를 사용합니다.

```console
// MDS 서버에서 실행
[root@MDS ~]# lctl get_param lod.*.dom_stripesize //DoM Stripe 크기를 확인
[root@MDS ~]# lctl get_param -P lod.*.dom_stripesize=2M //stripe 크기를 2M로 변경
//파라미터를 config에 저장
[root@MDS ~]# lctl conf_param <fsname>-MDT0000.lod.dom_stripesize=0
```

다음은 `DoM`을 구성했을 때 예제 그림과 이를 구성하는 명령어 입니다.

![DoM](/assets/DoM.PNG)
<center>그림 6. Data-On-MDT</center>

&nbsp;
  
```console
[root@Client ~]# lfs setstripe <--component-end| -E end1> <--layout | -L> mdt [<--component-end| -E end2> [STRIPE_OPTIONS] ...] <filename>
ex) [root@Client ~]#  lfs setstripe -E 1M -L mdt -E -1 -S 4M -c -1 /mnt/lustre/domfile // -S는 스트라이프 크기, -c는 스트라이프 개수

//구성 확인
[root@Client ~]# lfs getstripe /mnt/lustre/domfile
test2_domfile
  lcm_layout_gen:    2
  lcm_mirror_count:  1
  lcm_entry_count:   2
    lcme_id:             1
    lcme_mirror_id:      0
    lcme_flags:          init
    lcme_extent.e_start: 0
    lcme_extent.e_end:   1048576
      lmm_stripe_count:  0
      lmm_stripe_size:   1048576
      lmm_pattern:       mdt
      lmm_layout_gen:    0
      lmm_stripe_offset: 0

    lcme_id:             2
    lcme_mirror_id:      0
    lcme_flags:          0
    lcme_extent.e_start: 1048576
    lcme_extent.e_end:   EOF
      lmm_stripe_count:  -1
      lmm_stripe_size:   4194304
      lmm_pattern:       raid0
      lmm_layout_gen:    0
      lmm_stripe_offset: -1
```

&nbsp;

## DNE(Distributed Namespace Environment)

![DNE](/assets/DNE.PNG)
<center>그림 7. Distributed Namespace Environment</center>

&nbsp;

`HPC` 시스템은 일상적으로 수많은 클라이언트로 `Lustre`를 구성합니다. 이렇듯 클라이언트가 확장되었을 때 `MDT`도 추가로 확장 되어야합니다. `DNE`는 `MDT`가 추가되었을 때 분배하는 방법에 대해 말하고 있습니다. 

`lustre` version 2.4에서는 볼륨의 각 디렉터리 마다 `MDT`를 정해서 동시에 사용하는 구조 였지만, 버전 2.7 이 후에는 Single Directory환경에서 여러개의 Multiple MDT를 분산 형태로 사용할 수 있도록 변경되었습니다. 이를 `Lustre`에서는 단계별로 표현을 하고 있습니다. 1단계 Remote directories에서 `Lustre` 하위 디렉터리는 여러 `MDT`에 배포됩니다. 하위 디렉토리 배포는 관리자가 `Lustre`관련 `mkdir` 명령을 사용하여 정의합니다. 2단계 striped directories는 여러 `MDT`로 스트라이프된 디렉터리를 통해 `MDT`로 분배되어 저장됩니다. 이렇게 하면 단일 디렉터리 내에서 메타데이터 처리량을 확장할 수 있습니다.

`DNE` 시스템에서 `MDT`는 시간이 지남에 따라 불균형해질 수 있으며 사용자는 `MDT`를 추가/제거할 수 있습니다. `DNE`에서 restriping은 로드를 한 `MDT`에서 다른 `MDT`로 이동할때 사용됩니다. 

* 다음은 Striped Directory Migration 명령어입니다.

```console
[root@Client ~]# lfs migrate -m
ex) 아래 명령어는/testfs/largedir MDT0000에 있는 내용을 MDT0001 및 MDT0003으로 마이그레이션 하는 방법입니다.
[root@Client ~]# lfs migrate -m 1,3 /tetstfs/largedir
```

&nbsp;

# GPU Direct 스토리지 기술

![GPU Direct Storage](/assets/GPU_Direct_Storage.PNG)
<center>그림 8. GPU Direct Storage</center>

&nbsp;

오늘날 많은 연산을 사용하는 `빅데이터/AI` 분석을 가속화를 위해 `GPU Direct 스토리지` 기술이 등장하였습니다. 
`빅데이터/AI`에서는 많은 양의 데이터를 분석해야 하고, 이를 위해 데이터를 로드해야합니다. 이때, 소요되는 시간이 애플리케이션 성능에 영향을 미칠 수 있습니다. 이를 위해 `GPU Direct 스토리지`는 `NVMe or NVMe over Fabrics(NVMe-oF)`와 같은 로컬 또는 원격 스토리지와 `GPU` 메모리 사이에 데이터 경로를 생성합니다. 네트워크 어댑터 또는 스토리지와 가까운 `DMA(Direct Memory Access)`엔진을 활성화하여 CPU에 부담을 주지 않고 `GPU` 메모리로 데이터를 이동하는 기술입니다.

**GPU Direct 스토리지 기술을 lustre에서도 이번에 출시된 버전 2.15.0에서 지원한다고 합니다**(https://wiki.lustre.org/Lustre_2.15.0_Changelog).

* NVMe 이전 블러그 참고 : https://tech.gluesys.com/blog/2021/03/03/NVMe_1.html
* DMA : https://en.wikipedia.org/wiki/Direct_memory_access

&nbsp;

## GPU Direct 스토리지 이점

* `GPU` 기반 분석 어플리케이션의 병렬 스토리지 입출력 오버헤드를 최소화 하여 분석 시간을 획기적으로 단축할 수 있습니다.
  * `GPU` 연산 대기 시간 감소와 `PCI` 대역폭 최대 활용
  * 분석 시간 최소화
  * `CPU` 및 메모리 유효율 증가
  * 클라우드 리소스 활용성 최적화

&nbsp;

# 마치며

이번 포스팅에서는 lustre가 무엇인지 어떤 기능을 가지고 있는지와 GPU Direct Storage에 대해 간략하게 알아보았습니다. 다음 시간에서는 lustre FS을 구성하는 실습과 구성 후 각 기능을 이용한 테스트 및 성능 측정을 해보도록 하겠습니다. 감사합니다~👍

참고
---

* https://wiki.lustre.org/Introduction_to_Lustre
* https://wiki.whamcloud.com/display/PUB/Why+Use+Lustre
* https://wiki.lustre.org/Main_Page
* https://jaynamm.tistory.com/entry/Lustre-File-System
* https://github.com/DDNStorage/lustre_manual_markdown/blob/master/03.15-Hierarchical%20Storage%20Management%20(HSM).md
* https://www.sungardas.com/en-us/blog/what-is-hierarchical-storage-management/
* https://jira.whamcloud.com/browse/LU-10092
* https://wiki.lustre.org/images/0/04/LUG2018-Lustre_Persistent_Client_Cache-Xi.pdf
* https://wiki.lustre.org/images/b/b3/LUG2019-Lustre_Overstriping_Shared_Write_Performance-Farrell.pdf
* https://jira.whamcloud.com/browse/LUDOC-385
* https://wiki.lustre.org/images/c/c5/LUG2018-Small_File_IO_Perf_DataOnMDT-Gmitter.pdf
* https://wiki.whamcloud.com/display/PUB/DNE+1+Remote+Directories+High+Level+Design
* https://wiki.whamcloud.com/display/PUB/Remote+Directories+Solution+Architecture
* https://jira.whamcloud.com/browse/LU-1187?jql=text%20~%20%22DNE%22
* https://developer.nvidia.com/gpudirect-storage
