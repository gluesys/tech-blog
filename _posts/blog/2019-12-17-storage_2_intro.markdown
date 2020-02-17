---
layout:     post
title:      "스토리지 기초 지식 2편: 스토리지 프로토콜"
date:       2019-12-17
author:     박 주형 (jhpark@gluesys.com)
categories: blog
tags:       Fibre Channel, iSCSI, NFS, SMB, CIFS, RDMA, RoCE, iWARP, iSER
cover:      "/assets/server-farm-shot.jpg"
main:       "/assets/server-farm-shot.jpg"
---

## 목차

 * 파이버 채널
 * iSCSI
 * 분산 파일 시스템
 * RDMA
 
&nbsp;

앞선 시간에서는 전반적인 스토리지의 종류와 그 쓰임새를 알아봤는데요, 이번에는 스토리지 데이터를 공유하는 데 있어서 어떤 프로토콜들이 있는지 소개해 보고자 합니다.

&nbsp;

## 파이버 채널

파이버 채널(Fibre Channel, FC)은 기가비트 급의 전송 속도를 가진 네트워크 기술입니다. 처음 나왔을 당시에는 높은 트래픽을 처리하는데 TCP/IP 보다 빠르고, 스토리지 전용 네트워크로 대역폭을 확보할 수 있어 각광받은 기술입니다. 기존의 SCSI(Small Computer System Interface)프로토콜 기술이 응용되었으며, SAN 환경에서 iSCSI와 함께 블록 데이터를 전송할 때 가장 일반적으로 쓰입니다. 

&nbsp;

### 구성

파이버 채널 케이블에는 말 그대로 광학 섬유가 사용되지만 구리를 사용하는 경우도 있습니다. 해당 케이블을 통해 장비끼리 데이터를 주고받기 위해서는 HBA(Host Bus Adapter) 라는 인터페이스 카드를 필요로 합니다. 해당 카드가 장착된 스토리지를 파이버 채널 케이블로 파이버 채널 스위치와 연결하면 SAN 환경을 구성할 수가 있습니다.
파이버 채널의 가장 큰 특징은 파이버 채널의 데이터 단위인 프레임을 여러 개 엮어 시퀀스로 전송하고, 이러한 처리가 하드웨어 레벨에서 이루어져 CPU의 오버헤드를 줄일 수 있다는 점입니다. 또한 이더넷과는 달리 하드웨어 단에서 전송한 프레임의 무결성을 감지해 문제가 있을 경우 시퀀스를 재전송할 수 있습니다. 

&nbsp;

### FCoE

파이버 채널 오버 이더넷(Fibre Channel over Ethernet, 이하 FCoE)은 기존의 파이버 채널 프레임을 캡슐화해 이더넷 네트워크상에서 데이터를 주고받는 기술을 말합니다. 하나의 케이블과 인터페이스 카드로 이더넷과 파이버 채널 환경을 함께 구현할 수 있어 기존의 TCP/IP 네트워크 인프라를 유지한 상태에서 하드웨어 복잡성을 줄일 수 있다는 장점을 가지고 있습니다. 
FCoE의 도입은 2000년대 중반부터 Cisco사의 주도로 추진되어 왔습니다. 하지만 대체하고자 했던 이더넷의 속도가 비약적으로 발전함과 동시에 새로운 프로토콜의 도입을 꺼려하는 스토리지 회사들로 인해 현재로서는 기존 인프라를 대체하지 못하고 있는 상황입니다. 또한, 이 신기술을 도입하는 고객 입장에서도 통합 네트워크 어댑터(Converged Network Adapter, CNA)라는 인터페이스 카드와 FCoE 프로토콜을 지원하는 하드웨어가 필요해 비용 및 유지보수 측면에서도 불편함이 있습니다.

&nbsp;

## iSCSI

iSCSI(Internet Small Computer Systems Interface)는 기존 SAN 환경에서 파이버 채널이 가진 비용, 거리, 호환성 문제를 해결하고자 고안된 네트워크 기술입니다. 이름에서도 알 수 있듯이 이더넷 네트워크 상에서 SCSI 명령을 전달할 수 있어 LAN에서 WAN까지 스토리지의 접근성을 높였습니다. 

&nbsp;

### 구성

iSCSI는 기존의 이더넷 케이블이나 파이버 채널 케이블을 둘 다 사용할 수 있습니다. 또한, 필요에 따라 기존의 이더넷 NIC(Network Interface Card)나 iSCSI용 네트워크 카드(TCP Offload Engine과 iSCSI HBA)를 탑재해 서버 간에 블록 데이터를 공유할 수 있게 합니다. iSCSI는 파이버 채널과 달리 별도의 스위치가 필요 없이 이미 가지고 있는 이더넷 스위치로 SAN 환경을 구축할 수 있습니다. 
이처럼 기존 이더넷 인프라에서도 구축이 가능해 비용 및 전문인력이 부족한 중소기업에서 파이버 채널 SAN의 대안으로 사용되어 왔습니다. 현재 iSCSI는 성능과 안정성 면에 있어서 파이버 채널을 따라잡고 있으며, 요즘 스토리지 회사들은 블록 스토리지의 기본 프로토콜로서 파이버 채널과 함께 iSCSI를 제공하고 있습니다.

&nbsp;

## 분산 파일 시스템

파일 시스템은 저번 시간(링크)에서도 설명했듯이 블록보다 큰 단위로서 계층적 구조를 가지고 있습니다. 파일은 기본적으로 데이터와 그 데이터에 관한 데이터, 즉 메타데이터로 구성되는데요, 이 메타데이터를 통해 해당 파일의 유형, 위치, 접근 권한 등을 알 수 있습니다. 블록 스토리지의 경우는 위치정보 이외의 정보는 OS가 별도로 관리하게 되어 있어 이 부분이 주요 차이점이라 할 수 있습니다.
분산 파일 시스템(Distributed File System, DFS)은 네트워크를 통해 다수의 서버의 파일에 접근하여 공유하는 파일 시스템을 말합니다. 분산 파일 시스템에서는 네트워크에 연결된 여러 클라이언트 장비가 접근 권한을 통해 중앙 서버의 파일에 접근하는 방식을 취합니다. 원격의 스토리지를 케이블로 직접 연결해 사용한다는 느낌의 블록 스토리지 방식과는 달리, 분산 파일 시스템에서는 접근한 파일을 복사해 클라이언트의 캐시에 임시적으로 저장해 사용합니다. 
분산 파일 시스템에는 여러 종류가 있으며, 스토리지에 자주 사용되는 종류를 다음과 같이 소개해 보고자 합니다.

&nbsp;

### NFS

NFS(Network File System)는 네트워크를 통해 원격 서버와 파일을 주고받기 위해 개발된 최초의 분산 파일 시스템입니다. 썬 마이크로시스템즈(Sun Microsystems)에서 개발한 이 프로토콜은 UNIX 계열(Solaris, AIX, Linux 등) OS를 중심으로 macOS, 윈도우 등을 지원해 높은 범용성을 보입니다.

&nbsp;

### SMB/CIFS

SMB(Server Message Block)는 NFS와 같이 사용자에게 원격 서버의 파일에 접근하게 하는 파일 공유 프로토콜입니다. IBM에서 개발한 이 프로토콜은 윈도우 OS계열을 지원해 NFS와는 달리 윈도우에서 사용자 인증을 요구해 기본적으로 로그인이 필요하다는 차이점이 있습니다. SMB를 CIFS(Common Internet File System)와 병행해서 표기하는 경우가 있는데요, CIFS는 마이크로소프트가 SMB를 응용해 만든 프로토콜로 기본적으로 거의 같은 프로토콜이라고 할 수 있습니다. 하지만 요새 CIFS를 사용하는 스토리지 시스템은 거의 없다고 합니다. 
SMB/CIFS는 이와 같이 윈도우 계열 OS끼리의 파일 공유에 특화되어 있는데요, 기존의 UNIX 서버와 파일 및 프린터를 공유하기 위해서는 Samba라는 소프트웨어를 필요로 합니다. Samba는 UNIX 계열 서버에 탑재되며, 윈도우 및 맥과 같은 이기종 클라이언트와 SMB/CIFS 프로토콜을 통해 파일을 공유하고, 윈도우 서버를 대신해 도메인 컨트롤러 역할을 제공합니다. 

&nbsp;

## RDMA

RDMA(Remote Direct Memory Access)란 컴퓨터 간에 CPU를 거치지 않고 메모리끼리 직접 데이터를 주고받을 수 있게 하는 네트워크 기술을 말합니다. 전송 주체(initiator)에서 대상(target)으로 데이터를 전송할 시, 데이터의 임시복사 과정(NIC에서 어플리케이션 버퍼까지의 복사 과정)없이 바로 전송을 할 수 있습니다. 이로서 빠른 데이터 처리 속도와 낮은 네트워크 지연시간을 구현할 수 있어, 데이터 센터나 고성능 컴퓨터와 같이 대규모 데이터를 동시에 전송하는 환경에서 활용됩니다. 
RDMA는 iSCSI나 이더넷의 데이터 경로를 보완해 네트워크와 스토리지의 활용성을 높이기도 합니다. 이와 관련된 기술을 아래와 같이 소개해 보고자 합니다.

&nbsp;

### Infiniband

인터넷 서비스의 증가로 대용량 데이터 전송이 늘어나고 기존의 이더넷 규격이 이러한 인터넷 환경에 부응하지 못함에 따라 인피니밴드(Infiniband)라는 새로운 네트워크 규격이 고안되었습니다. 인피니밴드는 RDMA를 지원해 낮은 지연시간과 최대 50 Gbps의 높은 대역폭을 제공하는 새로운 네트워크 프로토콜입니다. 다수의 컴퓨터에 동시에 데이터를 전송하는 멀티캐스트 전송이 가능하며, 스토리지에서 고성능 컴퓨팅까지 저지연과 높은 대역폭이 요구되는 IT 환경에 주로 적용됩니다. 인피니밴드 네트워크 환경을 구성하기 위해서는 전용 스위치, 케이블, 어댑터 카드 등이 필요합니다. 

&nbsp;

### RoCE와 iWARP

RoCE(RDMA Over Converged Ethernet)는 이더넷에서 UDP를 통해 RDMA 통신을 제공하는 표준 네트워크 프로토콜입니다. iWARP(Internet Wide-area RDMA Protocol)는 RoCE와는 달리 RDMA 통신을 TCP를 통해 제공합니다. 이 두 프로토콜은 RDMA의 장점을 가짐과 동시에 기존 이더넷 환경에서 구축이 가능해 유연성과 비용면에서 장점을 가지고 있습니다. 하지만 iWARP의 경우 특유의 복잡한 구조로 RoCE와 같은 성능을 기대하기 힘들고 지원하는 벤더가 적어 많이 사용되지 않습니다. 

&nbsp;

### iSER

iSER(iSCSI Extensions for RDMA)는 iSCSI 프로토콜을 RDMA에 사용하기 위한 스토리지 프로토콜입니다. iSER는 인피니밴드, RoCE, iWARP과 같은 RDMA 프로토콜의 지원을 통해 기존 iSCSI에서 확장된 개념으로 매우 낮은 지연과 CPU 점유율 감소 등의 이점을 제공합니다. 기존의 iSCSI에 비해 성능 및 관리 측면에서 이점을 가지면서 iSCSI의 보안과 고가용성을 가지고 있습니다. 

&nbsp;

## 참고

FCoE: 
https://searchstorage.techtarget.com/definition/FCoE-Fibre-Channel-over-Ethernet
https://www.theregister.co.uk/2015/05/26/fcoe_is_dead_for_real_bro/

iSCSI:
https://searchstorage.techtarget.com/definition/iSCSI
https://www.kovarus.com/blog/servers-storage/lets-talk-iscsi/

File System:
https://en.wikipedia.org/wiki/Clustered_file_system#Distributed_file_systems
https://searchwindowsserver.techtarget.com/definition/distributed-file-system-DFS

RDMA
https://en.wikipedia.org/wiki/Remote_direct_memory_access
https://www.mellanox.com/related-docs/whitepapers/WP_Nueralytix_iSER.pdf

Infiniband
https://en.wikipedia.org/wiki/InfiniBand
https://edgeoptic.com/storage-protocols-comparison-fibre-channel-fcoe-infiniband-iscsi/

RoCE와 iWARP
https://www.mellanox.com/page/products_dyn?product_family=79&mtag=roce
https://www.theregister.co.uk/2016/04/11/nvme_fabric_speed_messaging/
https://www.mellanox.com/related-docs/whitepapers/WP_RoCE_vs_iWARP.pdf

iSER
https://en.wikipedia.org/wiki/ISCSI_Extensions_for_RDMA
https://www.linkedin.com/pulse/iser-iscsi-extensions-rdma-changing-landscape-ethernet-piyush-gupta/
https://mymellanox.force.com/mellanoxcommunity/s/article/what-is-iser-x
