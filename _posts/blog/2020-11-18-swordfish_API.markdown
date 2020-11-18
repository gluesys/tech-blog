---
layout:     post
title:      "스토리지 관리 인터페이스의 표준화, Swordfish"
date:       2020-11-18
categories: blog
author:     박주형 (jhpark@gluesys.com)
tags:       storage, management, Swordfish, 소드피쉬, 스토리지_관리, API, Redfish, SNIA, SMI-S
cover:      "/assets/swordfish.png"
main:       "/assets/swordfish.png"
---

기업의 스토리지 인프라를 관리하는 입장에서 관리의 편의성과 효율성은 서비스 계속성만큼이나 중요한 요소입니다. 기업의 IT 인프라를 확장하거나 통합하는 과정에서 부득이하게 타 벤더의 스토리지를 도입하거나 같은 벤더라도 호환이 안 되는 스토리지를 따로 관리해야 하는 경우가 발생합니다. 이렇게 되면 IT 인프라의 복잡도가 상승해 관리 효율이 떨어져 운영비용이 상승하게 됩니다.  

스토리지 업계에서는 이러한 이슈를 해결하기 위해 스토리지 시스템 관리에 있어서 산업 표준 API를 정의하는 방식을 도입해 왔습니다. 표준화된 스토리지 관리 API를 지원하면 한 벤더의 스토리지 관리 툴로 다른 벤더의 스토리지를 모니터링하고 관리할 수 있게 됩니다. 이러한 노력은 국제 비영리 산업단체인 SNIA(Storage Network Industry Association)에서 시작되었습니다.  

&nbsp;

## 스토리지 관리 표준화의 시도, SMI-S
  
이처럼 엣지에서 데이터를 어느 정도 정리해서 클라우드로 전송하거나 직접 대응하는 편이 클라우드에 걸리는 부하와 지연시간을 줄이고 적은 양의 데이터를 전송해 클라우드 이용 비용을 최소화할 수 있습니다. 유명 시장조사기관인 가트너(Gartner)에 의하면, 기존의 데이터센터나 클라우드 밖에서 생성 및 처리되는 SNIA는 2000년에 SMI-S(Storage Management Initiative Specification)라는 스토리지 관리 표준을 제시했습니다. 2007년에는 ISO 국제표준으로 지정되었고, 현재까지 1,350여 개의 스토리지 제품에서 지원하고 있어 상당히 오랫동안 쓰여온 표준이라고 할 수 있습니다. SMI-S는 기본적으로 하드웨어 기반의 관리를 제공하며, provider라는 엔드포인트를 제공해 클라이언트의 관리 소프트웨어와 소통합니다. 하지만 SMI-S는 SAN이나 NAS와 같이 전통적인 스토리지를 중점으로 디자인되었기 때문에 확장성 면에서 유연하지 못하고, 하이퍼컨버지드 인프라(HCI)와 같은 차세대 서버 아키텍처를 지원하기에는 한계가 있었습니다.  

&nbsp;

## Swordfish란?
    
Swordfish(정식 명칭은 Swordfish Scalable Storage Management API)는 이러한 차세대 스토리지에 부합하는 오픈된 스토리지 관리 표준으로, 2016년부터 SNIA에서 개발되고 있습니다. 기존의 벤더 중심적인 SMI-S와는 달리, 기능과 API를 사용자 중심적으로 디자인했습니다. 한마디로 IT 관리자는 이기종 스토리지 관리 환경에서 서비스 요구사항에 부합하는 스토리지 어레이나 가상머신을 직접 지정하기보다, 서비스 수준을 지정하는 것만으로 스토리지가 할당 가능해 사용자 편의성을 향상했습니다.  
  
Swordfish는 DMTF(Distributed Management Task Force)에서 제시한 Redfish 서버 관리 표준의 확장 개념으로 개발되었습니다. 간단히 말해 서버 관리 API인 Redfish에 스토리지 관리 부분이 Swordfish입니다. Redfish와 마찬가지로 JSON, OData, HTTPS 등 표준화된 기술들을 통해 REST 기반의 인터페이스를 제공하며, 표준화된 데이터 모델을 제공해 다양한 환경에서 스토리지 관리를 가능하게 합니다. 무엇보다 소규모의 파일 스토리지부터 HCI와 같은 가상화 환경이나 하이퍼스케일 데이터센터와 같은 고확장성 환경 등 어떤 규모의 스토리지 환경에서도 적용 가능합니다.  
  
이더넷과 파이버채널과 같은 네트워크를 포함해 SAS나 PCIe와 같은 스토리지 인터페이스도 지원하고 있고, RESTful API를 통한 블록, 파일, 오브젝트 스토리지에 대한 스토리지 관리를 제공해 높은 범용성을 가지고 있습니다. 특히 차세대 스토리지 및 네트워크 인터페이스로 주목받고 있는 NVMe와 NVMe-oF(NVMe over Fabric) 기반의 스토리지 시스템 관리도 지원하고 있습니다.  
  
이처럼 Swordfish는 오늘날 스토리지 아키텍처와 워크로드에 적합한 스토리지 관리 표준 API로, 기업 IT 인프라의 스토리지 운영관리를 통합해 더욱 단순하고 비용 효율적인 스토리지 시스템 운영이 가능할 것으로 보고 있습니다. 현재 델 EMC나 퓨어 스토리지 같은 대형 벤더뿐만 아니라 유니콘 기업들도 자사 스토리지 제품에 Swordfish를 도입하고 있는 추세입니다. 현재 Redfish가 IPMI를 점점 대체하고 있는 것처럼 앞으로 Swordfish도 SMI-S를 대체해 나갈 것으로 보입니다.  

&nbsp;

## 참고
  
SMI-S:  
 * https://www.enterprisestorageforum.com/storage-management/storage-management-and-standards.html
  
Swordfish:  
 * https://www.techrepublic.com/article/how-to-get-started-with-the-swordfish-storage-management-standard/
 * https://sniasmiblog.org/2019/06/storage-management-standards-matter/
 * https://vinfrastructure.it/2018/04/what-is-swordfish/
 * https://vinfrastructure.it/2018/04/what-is-redfish/
 * https://sciencelogic.com/blog/swordfish-part-1
 * https://searchstorage.techtarget.com/tip/Choose-the-right-storage-management-interface-for-you
 * https://www.snia.org/sites/default/files/technical_work/Swordfish/Swordfish_v1.2.1c_Specification.pdf
  
