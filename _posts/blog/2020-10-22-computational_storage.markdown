---
layout:     post
title:      "엣지 컴퓨팅 환경과 연산 스토리지"
date:       2020-10-22
categories: blog
author:     박주형 (jhpark@gluesys.com)
tags:       edge-computing, computational-storage, in-situ-processing, 연산-스토리지, 컴퓨테이셔널, 엣지-컴퓨팅, 엣지, 스토리지
cover:      "/assets/brain_circuit.jpg"
main:       "/assets/brain_circuit.jpg"
---

최근 디지털 트랜스포메이션이나 정부의 데이터 댐 사업 등 산업 전반에 걸친 디지털 인프라의 확장으로 엣지 컴퓨팅에 대한 기대가 높아지고 있습니다. 엣지 컴퓨팅에 대해 간단히 설명해 드리자면, 엣지 컴퓨팅(edge computing)은 기존에 클라우드에서 전부 받아서 처리할 데이터의 일부를 그 데이터 생성의 근원지인 엣지(가장자리)에 소재하는 서버 등의 컴퓨팅 장비에서 분담해서 처리한다는 개념입니다. 예를 들어, 조별 과제의 팀장 입장에서 팀원들이 조사한 자료를 취합할 때 단순히 웹사이트 링크나 이미지 복사-붙이기만 한 자료보다 내용을 요약해서 필요한 정보만 정리한 팀원의 자료가 나중에 정리하기 더 쉬울 것입니다.  

&nbsp;

## 엣지 환경에서의 스토리지
  
이처럼 엣지에서 데이터를 어느 정도 정리해서 클라우드로 전송하거나 직접 대응하는 편이 클라우드에 걸리는 부하와 지연시간을 줄이고 적은 양의 데이터를 전송해 클라우드 이용 비용을 최소화할 수 있습니다. 유명 시장조사기관인 가트너(Gartner)에 의하면, 기존의 데이터센터나 클라우드 밖에서 생성 및 처리되는 데이터의 양은 현재 전체 데이터의 10%인 반면에, 5년 후에는 75%까지 증가할 것으로 예상하고 있습니다. 5G 네트워크와 사물인터넷의 보편화로 폭증하는 데이터를 모두 클라우드에 전송하기에는 대역폭이나 비용 문제가 있고, 무엇보다 로컬에서 실시간으로 제공되어야 하는 서비스에서는 저 지연이 필수이기 때문입니다. 특히 엣지에서 AI 어플리케이션을 원활하게 실행하기 위해서는 일정 수준의 컴퓨팅 성능이 요구되고 있습니다.  
  
자율주행차를 예시로 들어보겠습니다. 자율주행차는 카메라와 각종 센서, 레이더 등에서부터 분당 대략 300GB의 데이터를 생성한다고 합니다. 하루 1시간씩 이용한다고 가정하면 매주 약 126TB의 데이터를 생성한다고 볼 수 있습니다. 이렇게 실시간으로 생성되는 데이터를 활용해 교통상황을 분석하고 실시간으로 위험 판단을 모두 엣지 서버의 CPU에서 감당하게 됩니다. 사실 이러한 수준의 데이터를 처리하려면 고가의 고성능 서버가 필요합니다만, 그러기에는 비용효율 측면에서 문제가 있습니다. 또한, 호스트의 CPU가 스토리지에 요청하는 데이터 규모가 클수록 내부 네트워크의 대역폭과 스토리지 IO 성능의 의존도가 높아지고 스토리지 병목이 발생할 수 있습니다. 게다가, 수집된 대규모 데이터에 대한 AI 전처리 작업 등의 무거운 워크로드를 호스트 CPU에서 실시간으로 처리하기에는 역부족일 수 있습니다.  

&nbsp;

## 연산 스토리지란?
    
연산 스토리지는 이러한 문제를 해결할 수 있는 기술이라고 할 수 있습니다. **연산 스토리지**, 또는 **컴퓨테이셔널 스토리지(computational storage)**는 간단히 말하자면 호스트 CPU에서 담당하던 연산 처리의 일부를 스토리지에서 분담해서 처리하는 아키텍처를 말합니다. 이러한 처리 방식을 인 시츄 프로세싱(in-situ processing)이라고도 합니다. 주로 NVMe SSD나 스토리지 컨트롤러와 같이 스토리지 장치 내에 CPU나 FPGA와 같은 연산 가속기(accelerator)가 내장되어 스토리지 수준에서 처리능력을 갖추게 됩니다. 기존에는 호스트에서 스토리지에 해당 데이터를 요청해 불러와서 처리하는 방식이었다면, 연산 스토리지가 도입된 아키텍처에서는 연산 할당량을 스토리지에서 일부 분담해서 신속하게 처리함과 동시에 불러오는 데이터의 양을 절감할 수 있어 대규모 데이터에 대한 처리속도를 가속할 수 있습니다. 이렇게 호스트에서 연산 스토리지의 연산 가속기로 오프로드 되는 스토리지 서비스를 연산 스토리지 서비스(computational storage service)라고 합니다. 
  
&nbsp;  

![Alt text](/assets/computational_storage_comparison.png){: width="600"}
<center>&#60;연산 스토리지의 구조&#62;</center>

&nbsp;

## 연산 스토리지의 종류
  
이러한 연산 스토리지의 개념을 몇몇 벤더들이 구현하기 시작하면서 SNIA (Storage Networking Industry Association)에서 연산 스토리지의 벤더 간 연동과 인터페이스 표준화를 정립하기 위해 Technical Working Group을 구성하기까지 이르렀습니다. 여기서 연산 스토리지 장치(computational storage device, CSx)를 다음과 같이 3가지 구성 방식으로 구분하고 있습니다.  

&nbsp;

![Alt text](/assets/computational_storage_type.png){: width="600"}
<center>&#60;연산 스토리지의 종류&#62;</center>

&nbsp;

우선, 연산 스토리지 프로세서(computational storage processor, CSP)는 위 그림과 같이 연산 가속기와 스토리지가 구분되면서 PCIe 네트워크에 연결된 형태를 말합니다. 다음에 연산 스토리지 드라이브(computational storage drive, CSD)는 보시는 바와 같이 연산 가속기가 스토리지 드라이브에 내장된 형태입니다. 현재 삼성전자와 NGD Systems에서 상용화하고 있고 가장 많이 보이는 연산 스토리지 장치입니다. 마지막으로 연산 스토리지 어레이(computational storage array, CSA)는 연산 가속기가 스토리지 컨트롤러나 PCIe 카드에 탑재되고 스토리지 드라이브가 브리지에 연결된 형태입니다. 연결되는 스토리지 드라이브는 일반 NVMe SSD가 될 수도 있고, 앞서 설명해 드린 연산 스토리지 드라이브가 될 수도 있습니다.  

현재 SNIA는 연산 스토리지를 통해 제공하는 스토리지 서비스를 고정 연산 스토리지 서비스(fixed computational storage services, FCSS)와 프로그램 변경식 연산 스토리지 서비스(programmable computational storage services, PCSS)로 구분하고 있습니다. FCSS는 암호화, RAID, 압축과 같이 정해진 기능을 제공하는 서비스를 말하며, PCSS는 사용자가 직접 프로그래밍이 가능한 연산 스토리지 서비스입니다.  

&nbsp;

## 마치며
  
연산 스토리지는 데이터 이동을 최소화해 전통적인 컴퓨팅-스토리지 방식에서 벗어난 방식으로 엣지 컴퓨팅의 효율을 극대화할 수 있습니다. 엣지 컴퓨팅을 활용하는 것으로 지연시간을 수 밀리초까지 줄일 수 있게 되지만, 연산 스토리지를 도입함으로써 그보다 더 낮은 초저지연을 구현할 수 있게 됩니다. 하지만 스토리지에서 컴퓨팅을 하게 되면서 앞으로 해결해야 하는 과제들이 있습니다. 우선, 스토리지에 연산 스토리지가 탑재됨으로써 호스트가 이를 인식할 수 있는 표준화된 API 등이 정립되어야 합니다. 그리고 이로 인해 아키텍처가 복잡해질 수 있고, 고성능과 저 지연의 필요성과 사용처는 비교적 한정적이라 할 수 있기 때문에 비용효율을 고려해야 합니다. 다음 포스트에서는 연산 스토리지의 연관 기술을 소개하고, 추가로 SNIA의 표준화 작업 중 Swordfish 스토리지 관리 API에 대해 다루어 보겠습니다.  

&nbsp;

## 참고
  
데이터 규모: 
 * https://www.gartner.com/smarterwithgartner/what-edge-computing-means-for-infrastructure-and-operations-leaders/
  
연산 스토리지 개념
 * https://www.nextplatform.com/2020/02/25/computational-storage-winds-its-way-towards-the-mainstream/
 * https://searchstorage.techtarget.com/definition/computational-storage#:~:text=Computational%20storage%20is%20an%20information,plane%20and%20the%20compute%20plane.
 * https://searchstorage.techtarget.com/tip/Computational-storage-may-ease-edge-storage-efforts#:~:text=Computing%20at%20the%20edge&text=By%20bringing%20data%20and%20applications,performance%20of%20mission%2Dcritical%20workloads.&text=Computational%20storage%20represents%20a%20huge,workloads%20running%20on%20the%20edge.
  