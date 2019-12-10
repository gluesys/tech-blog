---
layout:     post
title:      "인텔 옵테인 IMDT 기반 성능 테스트"
date:       2018-11-02 08:43:59
author:     김 경표 (hgichon@gmail.com)
categories: blog
tags:       Intel Optane Media Performance AnyStor SSD NVMe
cover:      "/assets/IntelOptaneIMDT.png"
main:      "/assets/IntelOptaneIMDT_main.jpg"
---

위 이미지는 인텔 사이트에서 발췌한 것임을 밝혀 둔다.
최근 인텔 옵테인 NVMe를 테스트할 기회가 생겼다. 설치 방법과 성능 결과를 간략히 정리해 본다.

## 옵테인 ?

옵테인이 뭔지 어떻게 다른지는 구글에서 찾아 보면 수 많은 자료가 있다.
나는 힘 좋고 오래 가는 밧데리... 아니 SSD로 정리해 보았고 가성비에 부응하는지 봐야겠다.
옵테인 활용 솔루션으로 두가지 정도가 눈의 띈다.

### CAS : 일반적인 캐시 소프트웨어

Linux md-cache와 같은 고속의 플래시 미디어를 HDD 기반 블럭 디바이스의 캐시로 사용할 수 있도록 해주는 소프트웨어 기반 솔루션.
SSD 제조사나 LSI/Adaptec 같은 RAID 컨트롤러 제조사 또는 여기저기서 캐시 소프트웨어를 제공하고 있다.
DM-Writeboost와 유사하게 DRAM을 1차 인덱싱 캐시로 사용하고 있어 전원이나 갑작스런 시스템 장애 시 재시작에 recovery 타임이 필요하다.
일반적인 SSD는 SLC 급을 제외하고 Endurence가 짧아 write intensive 워크로드에는 적합하지 않다고 알고 있다.
스펙 상의 옵테인은 Endurance가 좋아 캐시로 쓸만한 품질을 가지고 있어 보인다. 가격이 문제지만

###  IMDT : DRAM + Optane 한지붕 두가족 메모리 확장 OS?

캐시 소프트웨어는 워크로드에 따라 결과가 다양해서(극과 극) 범용 환경에서는 굳이 도입할 필요성이 있진 않았다.
헌데 캐시 영역이 확장된다면 쓸만한 영역이 많이 생기지 않을까 생각이 된다.
Intel에서 발표한 자료에 따르면 worst case에도 DRAM의 7~80% 수준이라고 하는데, 벌크 데이터 처리에 대한 자료는 없었던 바,
CIFS 프로토콜 I/O 처리를 page cache 수준에서 처리하는 경우의 성능 영향도를 살펴보아야 겠다.

## 설치

인텔의 [공식 설치 가이드](https://www.intel.com/content/dam/support/us/en/documents/memory-and-storage/intel-mdt-setup-guide.pdf){:target="_blank"}를 참고 했다.

* 사용한 옵테인: [P4800X 750GB 3D XPoint](https://www.intel.com/content/www/us/en/products/memory-storage/solid-state-drives/data-center-ssds/optane-dc-p4800x-series/p4800x-750gb-aic.html){:target="_blank"} x 2
* AnyStor-E 하드웨어: SuperMicro X10DRi / E5-2690v3 Dual / LSI-9361-8i (Samsung SSD 8 로컬 스토리지 용도) / Intel 10G 4 port (NFS/CIFS 성능 테스트 용도)
* 설치 순서 요약: 바이오스 설정 ==> 사용자 OS (여기서는 AnyStor-E 3.0) 설치 ==> 사용자 OS 상에서 Optane에 IMDT 설치 ==> Optane NVMe를 부팅 순서 상단으로 배치

OS에는 별다른 패치는 없음

* 참고 사항
  * DRAM과 옵테인은 1:8 크기만 가능 (현재 버전)
  * 옵테인은 최소 CPU 당 1개씩 필요 여러 장이 성능상 유리 (스트라이핑 하는 듯)
  * 메인보드가 Intel VT/VT-D를 지원하고 CPU 는 E5-x6xx 시리즈의 v3/v4 급이거나 최근 나온 scalable 시리즈일 것
  * IMDT용 OS 부팅 후 사용자 OS 부팅하는 구조
  * Optane NVMe 메모리 일부에 IMDT용 OS가 인스톨되므로(USB 부팅도 있다.), BIOS가 NVMe 디바이스로 부팅 가능해야 함.
  * Optane 메모리에 따라 IMDT가 설치된 버전이 있고, 사용자가 설치해야 하는 버전이 있음. 본 테스트에서는 직접 설치를 하였음.
  * IMDT 설치 시 카드별 라이선스가 필요하고, 설치 스크립트에서 라이센스를 입력받아 이메일을 통해 입력용 라이센스를 받아야 하는... 번거로움을 감수해야 함 - -
  * 사용한 [인스톨러](http://memorydrv.com/downloads/latest/){:target="_blank"}의 버전은 8.6.2535.77인데, 오늘자는 8.6.2535.100
  * 사용한 OS는 CentOS 7.5.1804 (AnyStor-E Custom)

## 테스트 개요

테스트 목적은 다음과 같다.

* 일반적인 리눅스 OS 운영에 문제가 없을까? 안 써본거라 노파심에... (/dev/shm을 타겟으로 하는 dd test, stress)
* Memory Intensive Performance Test (Intel 제공 툴)
* 4K UHD 편집 스토리지: 미디어 환경 테스트  (AJA system test / CIFS)

고려사항

* DATA wirte Intensive workload에서 페이지 캐시 플러시에 따른 process hang
* RSS 점유가 많은 프로세스의 시스템 응답성?

### 테스트 환경

* 구성도
* 클라이언트/ASE H/W 제원

### Linux shm dd 테스트 결과

* dd if=/dev/zero of=/dev/shm/100G bs=1024k count=102400
  * 850MB/s

### CIFS 미디어 테스트 결과

* 1 Client  : Write 600MB/s Read 450MB/s
* 7 Clients : Write 2.1GB/s Read 1.2GB/s

### Memory Performance Testing
