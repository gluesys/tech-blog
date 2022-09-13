---
layout:     post
title:      "TrueNAS SCALE의 설치부터 활용까지"
date:       2022-08-18
categories: blog
author:     박재일 (jipak@gluesys.com), 김진서 (jskim@gluesys.com)
tags:       [TrueNAS, Linux, ACL, CIFS, NFS, 파일서버]
cover:      "/assets/TrueNAS/Cover.png"
main:       "/assets/TrueNAS/Cover.png"
---

안녕하세요?
저는 6월에 글루시스의 기술팀에 입사한 김진서입니다.
IT업계에 뛰어들며 다양한 분야와 장비를 접해보았지만, NAS는 알고 있으면서 익숙하지 않았던 기술이기도 했습니다.
Synology NAS를 사용하던중 갑작스러운 전원보드의 고장으로 다른 NAS로 넘어가기 위해 NAS 및 운영체제를 공부하며 정리한 내용을 구독자 여러분에게 전달하고자 합니다.

먼저 Synology는 저에게 가장 익숙했습니다. 초기 구축비용이 높지만 Hardware와 Software가 완성된 기성품NAS이며 GUI기반의 전용 OS가 설치되어 개인 사용자 또는 작은 규모의 사무실에서 사용하기에 편리한 이점이 있습니다.

두 번째 로는 Linux 기반으로 공개된 기술을 활용하여 NAS를 구축하는 방법이 있습니다.
예를 들어 CentOS 또는 Ubuntu OS를 설치하여 필요한 환경에 맞게 FTP, CIFS(SMB), NFS 패키지를 설치하고 설정할 수 있습니다.

마지막으로 포스트의 목적인 Opensource 기반으로 개발되어 공개된 완전한 NAS 전용 운영체제를 사용해서 구축할 수 있습니다.
이러한 운영체제는 Synology처럼 NAS에 필수적인 요소들이 기본으로 제공되고, 편리하고 손쉬운 인터페이스로 구축할 수 있다는 장점이 있습니다.
Opensource 기반의 OS는 Open Media Vault, TrueNAS 등 다양하게 존재하지만 이 포스트에서는 좀 더 다양한 기능과 활용성 그리고 안정성을 갖춘 TrueNAS를 설치해 보고 사용하면서 느꼈던 장단점들과 활용 방법을 소개하도록 하겠습니다.

&nbsp;



## TrueNAS 설명
TrueNAS의 역사는 2005년부터 시작되었습니다. 당시에는 FreeNAS 라는 프로젝트로 시작되었으며, 2020년에 iXsystems에 의해 TrueNAS로 개발되어 왔습니다.

TrueNAS는 일반 CORE 버전, 엔터프라이즈 SCALE 버전이 있으며, 이 포스트에서는 SCALE 버전을 사용하였습니다.
TrueNAS는 FreeBSD를 기반으로 만들어졌으며, ZFS 파일시스템을 네이티브로 지원하고 Web GUI가 편리하고 직관적으로 제작되어 있어 시중에 판매되고 있는 NAS 제품들과 견줄만한 OS입니다.

오히려 Unix 운영체제를 잘 다루고, TrueNAS에 익숙해지면 가장 강력한 NAS OS라고 볼 수 있습니다.
또한 TrueNAS는 Hardware RAID Controller를 사용하지 않고도 그와 비슷한 성능과 안정성을 보장하는 특징이 있지만, 시스템 요구사항이 매우 높다는 단점도 존재합니다.

&nbsp;



## 테스트 시스템 소개
테스트에 사용된 시스템은 **Inspur**社의 장비입니다.
전체적인 사양은 아래와 같습니다.
||사양|
|---|---|
|CPU|Intel(R) Xeon(R) Silver 4310 CPU @ 2.10GHz *2|
|Memory|Total 32GB|
|Power Supply|800W * 2 Unit|
|Disk|Seagate Exos 12TB HDD * 12|

!(/assets/TrueNAS/01. Inspur/DashBoard.png)

Inspur 장비는 BMC(Baseboard Management Controller)를 통해 시스템의 전반적인 Status확인 및 Control을 할 수 있습니다.


!(/assets/TrueNAS/01. Inspur/System_Information.png)

시스템에 장착된 주요 Parts는 물론, Storage Disk의 상태까지 확인 가능하며, 일부 장비의 경우 시스템이 부팅된 상태에서도 Bios 옵션의 변경이 가능합니다.


!(/assets/TrueNAS/01. Inspur/Remote_Control.png)

BMC의 Remote Control 기능은 물리적인 KVM을 사용하지 않고 웹에서 서버의 제어가 가능합니다.
또한 물리적인 KVM이 설치되어 있더라도 관리해야 하는 서버가 많으면 KVM 케이블을 옮겨가며 작업하는 불편함이 있지만, Remote Control KVM을 활용하면 이런 불편함이 많이 해소되고, 다중 서버를 관리하기에 매우 편리한 이점이 있습니다.



## TrueNAS 설치
이제 본격적으로 TrueNAS의 설치를 진행해 보겠습니다.

TrueNAS 설치 이미지를 Rufus를 사용해 적당한 USB에 구워 부팅을 하면


!(/assets/TrueNAS/02. TrueNAS Install/Inspur_NF5280M6_BMT_Server_(TrueNAS)_OS_Install_1.png)

이런 화면이 보일 것입니다.
부팅을 위한 디스크를 선택하는 화면입니다.


!(/assets/TrueNAS/02. TrueNAS Install/Inspur_NF5280M6_BMT_Server_(TrueNAS)_OS_Install_2.png)

다음 화면은 루트 계정의 패스워드를 설정하는 화면입니다.
보안에 신경 써서 패스워드를 설정합니다.


!(/assets/TrueNAS/02. TrueNAS Install/Inspur_NF5280M6_BMT_Server_(TrueNAS)_OS_Install_5.png)

조금 기다려보면 위와 같이 설치가 완료된 화면이 보입니다.


!(/assets/TrueNAS/02. TrueNAS Install/Inspur_NF5280M6_BMT_Server_(TrueNAS)_OS_Start_2.png)

서버가 시작되면 위와 같은 화면이 보입니다.
네트워크부터 차례대로 진행하고, 서버를 리부팅하면 설치는 완료입니다.



## Dashboard
!(/assets/TrueNAS/03. TrueNAS_Dashboard/TrueNAS_Dashboard 001.png)

설치가 완료된 TrueNAS의 메인화면입니다. 시스템의 상태를 한눈에 볼 수 있습니다.
시스템 관리자에게 필요한 정보를 직관적으로 제공해주고 있습니다.



## Storage / Dataset
이제 실제 사용할 Storage Pool 및 Dataset을 만들어 보겠습니다.

!(/assets/TrueNAS/04. TrueNAS_Pool&Dataset/TrueNAS_Pool&Dataset_000.png)

먼저 Pool을 생성합니다.


!(/assets/TrueNAS/04. TrueNAS_Pool&Dataset/TrueNAS_Pool&Dataset_001.png)

생성된 Pool ‘vg’ 의 우측의 메뉴를 열어 Add Dataset을 실행합니다.


!(/assets/TrueNAS/04. TrueNAS_Pool&Dataset/TrueNAS_Pool&Dataset_003.png)

목적에 맞게 비어있는 필드를 채워줍니다.

!(/assets/TrueNAS/04. TrueNAS_Pool&Dataset/TrueNAS_Pool&Dataset_005.png)

이제 Share로 이동, Windows (SMB) Shares에서 Add를 눌러 CIFS/SMB 공유를 만들어 줘야 합니다.



## ACL ( Access Control List)
그룹별 / 사용자별 권한을 제어해보겠습니다.
시나리오는 아래와 같습니다.

|개발팀(DEV)|영업팀(SALE)|기술팀(TECH)|

세 가지 부서가 있으며, 각각 전용 폴더를 생성합니다.
그리고 타 부서의 전용폴더는 서로 접속을 못 하도록 접근제한을 설정해 놓습니다.


!(/assets/TrueNAS/05. TrueNAS_User_Group/TrueNAS_User_Group_001.png)

저는 DEV / SALE / TECH 로 그룹을 만들었습니다.


!(/assets/TrueNAS/05. TrueNAS_User_Group/TrueNAS_User_Group_002.png)

SALE1 / SALE2 / DEV1 / DEV2 / TECH1 / TECH2 유저를 만들었습니다.


!(/assets/TrueNAS/05. TrueNAS_User_Group/TrueNAS_User_Group_003.png)

유저를 생성할 때 원하는 그룹에 종속되게 할 수 있습니다.


!(/assets/TrueNAS/05. TrueNAS_User_Group/TrueNAS_User_Group_004.png)

!(/assets/TrueNAS/05. TrueNAS_User_Group/TrueNAS_User_Group_005.png)

물론 모든 유저를 다 만든 후, 그룹속성에서 원하는 유저를 종속시키는 것도 가능합니다.



## SMB / CIFS
이제 Windows System에서 SMB를 통해 공유폴더에 접속해보겠습니다.

!(/assets/TrueNAS/06. TrueNAS_SHARE/TrueNAS_Share_003.png)

생성한 Dataset에서 View Permissions 로 들어갑니다.


!(/assets/TrueNAS/06. TrueNAS_SHARE/TrueNAS_Share_004.png)

연필 모양으로 된 Edit 버튼을 눌러줍니다.


!(/assets/TrueNAS/06. TrueNAS_SHARE/TrueNAS_Share_005.png)

!(/assets/TrueNAS/06. TrueNAS_SHARE/TrueNAS_Share_007.png)

Add Item을 선택하여 만들어두었던 그룹 또는 유저를 추가합니다.


!(/assets/TrueNAS/06. TrueNAS_SHARE/TrueNAS_Share_008.png)

!(/assets/TrueNAS/06. TrueNAS_SHARE/TrueNAS_Share_009.png)

!(/assets/TrueNAS/06. TrueNAS_SHARE/TrueNAS_Share_010.png)

권한을 제대로 설정했다면 각 부서별 전용폴더를 만들 수 있습니다.



## NFS MOUNT
이제 Linux System에서 마운트를 해보겠습니다.

!(/assets/TrueNAS/07. TrueNAS_NFS_MOUNT/TrueNAS_NFS_MOUNT_001.png)

'''df -h'''
현재 시스템의 파일시스템을 확인 합니다.

'''Mkdir nfs_test'''
nfs test 폴더를 생성합니다.

'''showmount -e 192.168.53.253'''
TrueNAS 서버에서 마운트가 가능한 폴더를 확인합니다.

'''Mount -t nfs 192.168.53.253:/mnt/vg/test_dev /mnt/nfs_test'''
192.166.53.253 서버의 mnt > vg > test_dev 폴더를, 클라이언트 서버의 mnt > nfs_test 폴더에 마운트 합니다.

'''df -h'''
제대로 마운트가 되었는지 확인합니다.

!(/assets/TrueNAS/07. TrueNAS_NFS_MOUNT/TrueNAS_NFS_MOUNT_002.png)

마운트 후, 폴더가 생성되는지 시도해봅니다.


!(/assets/TrueNAS/07. TrueNAS_NFS_MOUNT/TrueNAS_NFS_MOUNT_003.png)

윈도우 SMB 에서도 방금 생성한 'new_folder' 가 잘 보이는군요.



## Virtual Machines
TrueNAS는 VMware와 같은 가상머신 기능을 지원하고 있습니다.

!(/assets/TrueNAS/08. TrueNAS_Virtual Machines/TrueNAS_Virtual Machines_001.png)

VM 생성을 해보겠습니다.


!(/assets/TrueNAS/08. TrueNAS_Virtual Machines/TrueNAS_Virtual Machines_002.png)

순서는 VMware 가상화 어플리케이션과 크게 다르지 않습니다.


!(/assets/TrueNAS/08. TrueNAS_Virtual Machines/TrueNAS_Virtual Machines_003.png)

!(/assets/TrueNAS/08. TrueNAS_Virtual Machines/TrueNAS_Virtual Machines_004.png)

!(/assets/TrueNAS/08. TrueNAS_Virtual Machines/TrueNAS_Virtual Machines_005.png)

!(/assets/TrueNAS/08. TrueNAS_Virtual Machines/TrueNAS_Virtual Machines_006.png)

미리 서버에 업로드 해두었던 ISO를 사용하여 바로 OS설치가 가능합니다.


!(/assets/TrueNAS/08. TrueNAS_Virtual Machines/TrueNAS_Virtual Machines_007.png)

!(/assets/TrueNAS/08. TrueNAS_Virtual Machines/TrueNAS_Virtual Machines_008.png)

생성이 완료된 VM의 모습입니다.



## Media Server

!(/assets/TrueNAS/09. Media Server/001.png)

사실상 NAS활용의 가장많은 비중을 차지하고 있는 활용방법이라고 생각합니다.


!(/assets/TrueNAS/09. Media Server/003.png)

크고 광활한 TB 규모의 스토리지에 영상, 영화, 음악, 사진등을 업로드 하여 용량의 제한에서 벗어나거나
트랜스코딩을 활용하여 4K 해상도의 고용량 영상을 모바일 디바이스에 맞게 해상도를 낮춰 재생을 하거나


!(/assets/TrueNAS/09. Media Server/000.jpg)

WebOS를 탑재한 스마트TV, 프로젝터 등에서 지원하지 않는 코덱의 영상을 트랜스코딩하여 재생합니다.
저 또한 NAS활용의 주된 목적이기도 합니다.


!(/assets/TrueNAS/02. TrueNAS Install/Inspur_NF5280M6_BMT_Server_(TrueNAS)_Apps.png)

TrueNAS의 Apps에는 Plex Media Server가 있습니다.


!(/assets/TrueNAS/09. Media Server/002.png)

이를 설치하면 Plex가 자동으로 컨텐츠를 분류하고, 컨텐츠의 내용을 스크랩해서 포스터와 줄거리를 소개해주는 미려한 Media Server를 구성합니다.



## Smart Home Server

최근에는 보안과 방범을 위해 IoT카메라등을 설치하는 곳이 늘어나고 있습니다.
저 역시 IoT장비를 작업실, 오피스텔등 곳곳에 설치하였습니다.
이러한 장비들은 전용 어플리케이션을 사용해야 하고, 제조업체의 클라우드 서버를 거쳐야 모니터링 하거나 제어를 할수있는 단점이 있습니다.

클라우드 서버를 거침에 따라서 Latency와 보안의 문제점이 발생합니다.
이러한 문제를 해결하기 위해 로컬서버에 장비를 등록하여, 모니터링과 제어를 할수있는 플랫폼을 설치할수도 있습니다.


!(/assets/TrueNAS/09. Media Server/001.png)

가상머신에 스마트홈 서버를 설치하여 구동하는 모습입니다.
IoT장비의 제조업체는 수십~수백가지가 되는데요, 대부분 API를 제공하고 있기 때문에 계정연동을 하거나, 스마트홈 서버에 바로등록도 가능합니다.


## 마치며
이 포스트에서 다루지 못한 Docker와 수십가지의 Third Party Plugin가 많이 있습니다.
고성능 고사양의 장비에 TrueNAS를 설치한다면 다재다능한 다목적 서버로 사용하기에 손색이 없다고 할 수 있습니다.

이 포스트는 글루시스에 입사하여 처음 작성한 포스트입니다.
처음 글을 시작했을 때는 막막했지만 선배들의 도움으로 많이 다듬어졌습니다.
그럼에도 많이 부족하고, 아쉬움이 많이 남는 글입니다.
다음에 기회가 된다면 Docker의 활용과 TrueNAS의 숨은 활용방법들을 소개하고 싶습니다.