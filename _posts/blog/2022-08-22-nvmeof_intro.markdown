---
layout:     post

title:      "NVMe 오버 패브릭(NVMe-oF)이란?"
date:       2022-08-22

author:     박주형 (jhpark@gluesys.com)
categories: blog
tags:       [NVMe, NVMe-oF, NVMe over Fabrics, RDMA, Storage, SSD, RoCE, iWARP, 파이버 채널, Fibre Channel, 이더넷, Ethernet, TCP]
cover:      "/assets/nvmeof_maincover.jpg"
main:       "/assets/nvmeof_maincover.jpg"
---

&nbsp;
  
현재 스토리지 인터페이스의 주류인 SATA/SAS 인터페이스는 플래터가 회전하면서 물리적인 디스크 판으로부터 데이터를 읽고 쓰는 하드디스크에 최적화되었기 때문에, 전기 신호로 데이터를 읽고 쓰는 플래시 타입의 SSD에 적합하지 않습니다. 하드디스크의 헤드 탐색시간이나 회전 지연 시간 설정과 같이 물리적인 입출력 구조를 갖지 않는 SSD에서는 I/O 요청 과정에 불필요한 작업이 포함되어 있고, 명령어 큐 또한 순차적으로 처리하기 때문에 병렬 접근이 가능한 플래시의 본래 성능을 끌어내기 어려웠습니다. 여기서 등장하게 된 새로운 인터페이스가 바로 **NVMe(Non-Volatile Memory Express)** 입니다.  
  
첫 NVMe 칩셋이 등장한 2012년 8월부터[^1] 정확히 10년 후인 지금, NVMe는 SSD 기술을 주도하는 핵심 프로토콜이 되었습니다. 시장조사 기관에 의하면, NVMe SSD는 이미 2018년에 기업용 SSD 시장에서 SATA나 SAS 기반의 SSD를 넘어 40%의 점유율을 기록한 바 있습니다[^2]. 이처럼 NVMe 기술은 일반 소비자 시장을 넘어 기업의 데이터센터에서도 폭 넓게 활용되고 있습니다. SSD의 가격은 날이 갈수록 낮아짐과 동시에, 현재 쓰이는 PCIe 4.0 대비 1.5배 빠른 PCIe 5.0 기반의 NVMe SSD가 공개되면서, NVMe SSD가 차세대 주류 스토리지로써 자리잡을 날도 얼마 남지 않아 보입니다.  
  
초창기에는 NVMe SSD 스토리지 미디어를 직접 연결(DAS) 방식으로 사용했습니다. 하지만, NVMe 프로토콜의 이점이 스토리지 벤더의 하드웨어에 종속된 어플라이언스에만 한정되고, NVMe SSD로 구성된 고속의 스토리지를 공유 방식이 아닌 독립적으로만 사용하기에는 비용 대비 효율이 떨어진다는 문제가 있습니다.  이러한 NVMe 프로토콜을 네트워크 프로토콜로 활용하고자 **NVMe over Fabrics** 기술이 제시되었습니다.  

&nbsp;

## NVMe-oF 소개
  
**NVMe over Fabrics(이하 NVMe-oF)**는 말 그대로 NVMe 프로토콜로 다양한 네트워크들(fabrics)을 통해 NVMe 장치들을 연결할 수 있게 해주는 네트워크 프로토콜의 개념입니다. 쉽게 말해, NVMe-oF는 네트워크를 통해 NVMe 프로토콜로 원격 장치에 접근하는 방식이라고 볼 수 있습니다. NVMe-oF는 지난 2016년, NVMe 사양을 정의한 NVM Express Inc.에서 1.0 버전을 공개했고, 가장 최근 버전인 1.1은 2019년에 NVMe 1.4 버전과 함께 공개되었습니다.  
  
NVMe 프로토콜은 로컬의 PCIe 스위치나 PCIe 버스를 통해 NVMe 장치들에 접근하지만, NVMe-oF 기술을 활용하면 파이버 채널이나 이더넷과 같은 네트워크를 통해 네트워크 상에 존재하는 NVMe 장치에도 접근할 수 있게 됩니다. 무엇보다, NVMe-oF는 전용 네트워크가 아닌 기존의 파이버 채널과 이더넷 환경을 활용하기 때문에 별도의 네트워크 환경을 추가로 도입할 필요가 없습니다.  
  
&nbsp;
  
### NVMe-oF 유형
  
NVMe-oF는 파이버 채널과 이더넷 기반의 RDMA 및 TCP/IP 환경에서 활용할 수 있습니다.  
  
#### NVMe/FC
  
파이버 채널을 활용하는 **NVMe/FC**는 기존에 파이버 채널이 구축된 환경에서 도입이 가능합니다. 파이버 채널은 기본적으로 SCSI와 NVMe 프로토콜을 동시에 매핑 가능하기 때문에, 파이버 채널 기반의 인프라를 보유한 데이터센터에서 스위치의 소프트웨어 업그레이드를 통해 쉽게 도입할 수 있습니다. 다만, 이더넷 기반의 인프라에 비해 외부 네트워크와의 연결이 제한적이고, 캡슐화된 SCSI 명령어를 NVMe 명령어로 변환하는 과정으로 인해 성능 저하가 발생합니다.  
  
&nbsp;

#### NVMe/RDMA
  
이더넷을 활용하는 NVMe-oF는 기본적으로 RDMA 기술을 활용합니다. 이전 포스트인 [스토리지 기초 지식 2편: 스토리지 프로토콜](https://tech.gluesys.com/blog/2019/12/17/storage_2_intro.html) 에서도 다루었습니다만, **RDMA(Remote Direct Memory Access)**는 같은 네트워크 상에 있는 서버 간의 메모리에 CPU를 거치지 않고 접근할 수 있는 기술입니다. **NVMe/RDMA** 환경에서는 주로 **RoCE(RDMA over Converged Ethernet)**나 **iWARP(Internet Wide-area RDMA Protocol)**와 같은 네트워크 프로토콜을 통해 NVMe-oF 프로토콜 패킷을 캡슐화하여 전송합니다.  
  
기존에 이더넷 기반 인프라를 보유하고 있는 경우에는 네트워크 카드 추가 구축을 통해 도입이 가능하고, NVMe/RoCE의 경우에는 주로 매우 낮은 지연 시간을 목표로 물리적으로 컴퓨팅 자원과 가깝게 단일 랙 환경에서 구축합니다. 이러한 RDMA 기반의 NVMe-oF는 워크로드 유형이나 인프라 규모에 따라 비교적 낮은 CPU 사용률과 마이크로초 수준의 지연 시간(latency)을 제공하지만, 확장성에 있어서는 NVMe/FC나 NVMe/TCP에 비해 떨어지는 단점이 있습니다.  
  
&nbsp;

#### NVMe/TCP
  
최근에는 TCP/IP를 기반으로 하는 **NVMe/TCP**가 주목받고 있습니다. 기존의 이더넷이나 파이버 채널 기반의 NVMe-oF를 도입하는 경우, 별도의 호스트 어댑터나 드라이버 등의 조정이 필요해, 비용 및 복잡도 문제가 있었습니다. 하지만, NVMe-oF 1.1 버전에서부터 TCP 전송 바인딩을 지원하게 되면서 TCP/IP를 통해 NVMe-oF 프로토콜 패킷을 캡슐화하여 전송할 수 있게 되었습니다.  
  
TCP 전송 바인딩은 어떠한 이더넷 네트워크 상에서도 사용할 수 있기 때문에 어떠한 표준 이더넷 어댑터나 범용 하드웨어와도 호환된다는 이점이 있습니다. 이로 인해, NVMe-oF를 별도의 설정 없이 도입하고 확장할 수 있습니다. 특히, 기존 인프라가 파이버 채널 기반이 아니거나, RDMA를 사용하지 않는 이더넷 기반 인프라에 NVMe-oF를 도입할 수 있습니다. NVMe/TCP는 아직 파이버 채널이나 RDMA 기반 NVMe-oF 수준의 저 지연에 미치지는 못하지만, 확장성과 범용성에 있어서는 우위를 가지고 있습니다. 특히 초기에 비싼 비용으로 NVMe 기반 플래시 어레이를 도입한 기업의 경우, 별도의 추가 네트워크 구축 없이 TCP/IP 네트워크를 통해 NVMe 플래시 어레이의 NVMe 스토리지 자원을 공유할 수 있게 되었습니다.  
  
&nbsp;

|      | NVMe/FC | NVMe/RDMA | NVMe/TCP |
| :--- | :--- | :--- | :--- |
| 하드웨어 요구사항 | 파이버 채널 환경 | PFC가 구성된 이더넷 환경(RoCE)이나, IP 기반의 이더넷 환경(iWARP) | 이더넷 환경 |
| RDMA 지원 여부 | 미지원 | 지원 | 미지원 |
| 초기 구축 비용 | 파이버 채널 스위치 및 HBA 펌웨어/소프트웨어 업그레이드 필요 | 이더넷 스위치에서 PFC 지원 필요 | 없음 |
| 성능 | 높음 | 매우 높음 | 보통 |
| 확장성 | 보통 | 낮음 | 높음 |

&nbsp;

### NVMe-oF의 활용 전망
  
NVMe-oF 도입의 가장 큰 목적은 바로 NVMe 기반의 분산 스토리지 네트워크를 형성해 원격의 NVMe 장치의 지연 시간을 로컬 수준으로 구현할 수 있다는 것입니다. 이로 인해 고성능 저 지연 스토리지 워크로드를 필요로 하는 대규모 데이터센터에서 수요가 있을 것으로 보입니다. 특히 AI/머신러닝 분야에서 대규모 데이터셋을 훈련 시키는 경우 GPU의 성능에 따라 병목이 발생할 수 있는데, NVMe-oF를 활용하면 GPU가 NVMe 스토리지 풀에 직접 접근할 수 있어 분석 애플리케이션이 동일 시간 내에 더욱 많은 데이터를 처리할 수 있게 됩니다. 또한, 전자상거래나 금융기관과 같이 데이터베이스에 대한 초저지연 접근을 요구하는 환경에서도 파이버 채널이나 RDMA 기반의 NVMe-oF 기술이 도입되고 있습니다.  
  
현재 구성된 네트워크 인프라에서 NVMe SSD가 탑재된 고성능 스토리지를 활용할 계획이 있을 경우, 다음과 같은 방법으로 접근한다면 비용 절감에 도움이 될 것 같습니다.  
먼저 이더넷 환경의 경우, NVMe 스토리지를 이터넷 스위치에 연결 후 NVMe/TCP를 이용하면 스토리지 외 추가 장비 없이도 기존 서버에서 접근할 수 있습니다. 이후 NVMe 스토리지의 요구사항이 높아지게 되면 한 단계 높은 대역폭을 갖는 이더넷 네트워크로 확장하거나, 인피니밴드를 이용한 별도의 네트워크를 추가로 구성하는 방법이 있겠습니다.
파이버 채널 환경의 경우에도 동일하게 NVMe 스토리지를 파이버 채널 스위치와 연결한 후, NVMe/FC를 이용하면 서버에서 접근할 수 있습니다. 이후 사용 빈도가 높아질 경우에는 마찬가지로 별도의 네트워크 확장을 통해 서버의 요구사항을 만족할 수 있습니다.
  
NVMe-oF와 다른 오픈형 표준들과의 연계도 눈여겨볼 수 있습니다. 현재 리눅스 커널과 **SPDK**는 NVMe-oF 이니시에이터와 타겟 드라이버를 제공하며, RoCE와 TCP 전송을 지원하고 있습니다. 특히 SPDK는 NVMe SSD가 가진 본연의 성능을 뽑아 내기 위해 디자인된 오픈소스 개발 키트로, 입출력 성능 최적화 및 CPU 리소스 절약을 구현할 수 있습니다. 또한, 성능에 영향 없이 특정 벤더 제품을 위한 NVMe 기능들을 사용할 수 있게 해주며, 기존 소프트웨어 모듈에 대한 API를 제공해 커스터마이징이 용이합니다.  
  
[지난 포스트](https://tech.gluesys.com/blog/2021/11/15/cxl_1.html) 에서 다룬 **CXL(Compute Express Link)** 인터커넥트의 경우, NVMe와 같이 PCIe를 활용하긴 하지만, 한동안은 경쟁보다는 공존할 것으로 보입니다. CXL은 호스트 프로세서와 CXL 장치 간 메모리를 공유할 수 있어 서버 내 메모리 자원의 범용성과 확장성을 제공합니다. 이러한 메모리 공유에 있어서 NVMe 프로토콜은 레거시 블록 스토리지를 지원하는 역할을 할 수 있습니다. 또한, NVMe-oF도 같은 PCIe 기반의 기술이다 보니 어느 한쪽 기술을 사용하는데 있어서 특정 기술에 한정되는 것에 대한 우려가 적다고 볼 수 있습니다.  
  
&nbsp;

## 마치며
  
클라우드와 고성능 컴퓨팅 환경이 점차 보편화되면서 데이터센터 내 스토리지 성능에 대한 요구는 점점 커져가고 있습니다. NVMe-oF는 NVMe 장치를 노드 바깥의 네트워크 상에서 접근할 수 있게하여 차세대 플래시 미디어의 표준이 될 NVMe 기술을 한 단계 업그레이드했다는 평가를 받고 있습니다. NVMe-oF는 아직 등장한지 얼마 안 된 기술로, 도입 시 일부는 추가 장비나 업그레이드, 설정 작업 등이 요구되어 성능 최적화 및 비용 문제에서 완전히 벗어나지는 못했지만, 산업 전반에서의 투자와 지지를 고려하면 기술에 대한 성숙도는 점차 깊어질 것으로 보입니다.  


&nbsp;

## 참고

---

 * https://www.techtarget.com/searchstorage/definition/NVMe-over-Fabrics-Nonvolatile-Memory-Express-over-Fabrics
 * https://www.eetimes.eu/nvme-of-is-ready-to-go-the-distance/
 * https://blog.westerndigital.com/nvme-of-explained/
 * https://nvmexpress.org/answering-your-questions-nvme-of-1-1-specification-key-features-and-use-cases-webcast/
 * https://www.snia.org/sites/default/files/PM-Summit/2020/presentations/08_Perfect_Trifecta_Mittal_Shadley_final_PM_Summit_2020.pdf
 * https://www.computerweekly.com/feature/Five-things-you-need-to-know-about-NVMe-over-Fabrics

&nbsp;

## 각주

---

[^1]: https://en.wikipedia.org/wiki/NVM_Express#NVMe-oF:~:text=The%20first%20commercially%20available%20NVMe%20chipsets%20were%20released%20by%20Integrated%20Device%20Technology%20(89HF16P04AG3%20and%2089HF32P08AG3)%20in%20August%202012
[^2]:	https://www.techtarget.com/searchstorage/news/252458395/New-NVMe-Western-Digital-SSDs-target-cloud-hyperscale-and-edge 
  