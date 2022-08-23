---
layout:     post
title:      "TrueNAS의 설치부터 활용까지"
date:       2022-08-18
categories: blog
author:     박재일 (jipak@gluesys.com), 김진서 (jskim@gluesys.com)
tags:       [TrueNAS, Linux, ACL, CIFS, NFS, 파일서버]
cover:
main:
---

NAS OS 는 생각보다 많이 있습니다.

1.초기 구축비용은 비싸지만 GUI 기반의 OS가 설치되어 일반 개인사용자 및 소호 사무실에서 사용하기에 편리하고 쉬운 시놀로지

2.가장 손쉽게 구성할 수 있고, 무료인 리눅스 CentOS를 설치하여 입맛에 맞게 FTP, CIFS, NFS 패키지를 설치하고 세팅하는 방법.

3.무료 오픈소스 이면서 강력한 성능의 TrueNAS 등 여러종류가 있습니다.
이 포스트 에서는 TrueNAS의 설치부터 활용까지 다뤄보겠습니다.

&nbsp;

## TrueNAS 설명
TrueNAS는 일반사용자용 CORE 버전, 엔터프라이즈 사용자용 SCALE 버전이 있으며, 이 포스팅 에서는 SCALE 버전을 사용하였습니다.
TrueNAS는 FreeBSD를 기반으로 만들어졌으며, ZFS 파일시스템을 네이티브로 지원하고 WEB GUI 가 상당히 편리하고 직관적으로 제작되어 있어 시중에 판매되고 있는 NAS 제품들과 견줄만한 OS입니다. 오히려 UNIX 운영체제를 잘 다룬다면 가장 강력한 NAS OS라고 볼 수 있습니다.
또한 TrueNAS는 하드웨어 RAID CONTROLLER를 사용하지 않고도 그와 비슷한 성능과 안정성을 보장하는 특징이 있지만, 시스템 요구사항이 매우 높다는 단점도 존재합니다.

&nbsp;

## 테스트 시스템 소개
테스트에 사용된 시스템은 **Inspur**社의 장비입니다.
전체적인 사양은 아래와 같습니다.
CPU : Intel(R) Xeon(R) Silver 4310 CPU @ 2.10GHz X2
RAM : 32GB
PSU : 800W X2
HDD : Seagate Exos 12TB X 12

!(/assets/TrueNAS/01. Inspur/DashBoard.png)
Inspur 장비는 BMC ( Baseboard Management Controller )를 통해 시스템 전반적인 상태확인 및 컨트롤을 할 수 있습니다.

!(/assets/TrueNAS/01. Inspur/System_Information.png)
시스템에 장착된 파츠는 물론, 스토리지의 상태역시 확인 가능합니다.

!(/assets/TrueNAS/01. Inspur/Remote_Control.png)
BMC의 Remote Control 기능은 물리적인 KVM을 설치하지 않아도 웹상에서 서버를 제어할 수 있습니다.
물리적인 KVM이 설치되어 있더라도 관리해야될 서버가 많을때는 KVM 케이블을 옮겨가며 작업하는 번거로움이 있지만, Remote Control KVM을 활용하면 이런 불편함이 많이 감소합니다.

&nbsp;

## TrueNAS 설치
자, 이제 본격적으로 TrueNAS 의 설치를 진행 해보겠습니다.

TrueNAS 설치 이미지를 RUFUS를 사용해 적당한 USB에 구워둔 다음 부팅을 하면
!(/assets/TrueNAS/02. TrueNAS Install/Inspur_NF5280M6_BMT_Server_(TrueNAS)_OS_Install_1.png)
이런 화면이 보일 것 입니다, 부팅을 위한 디스크를 선택하는 화면입니다.

!(/assets/TrueNAS/02. TrueNAS Install/Inspur_NF5280M6_BMT_Server_(TrueNAS)_OS_Install_2.png)
다음 화면은 루트 계정의 패스워드를 설정하는 화면입니다. 보안에 신경써서 패스워드를 설정합시다.

!(/assets/TrueNAS/02. TrueNAS Install/Inspur_NF5280M6_BMT_Server_(TrueNAS)_OS_Install_5.png)
조금 기다려보면 위와 같이 설치가 완료된 화면이 보입니다.

!(/assets/TrueNAS/02. TrueNAS Install/Inspur_NF5280M6_BMT_Server_(TrueNAS)_OS_Start_2.png)
서버가 시작되면 위와 같은 화면이 보입니다.
네트워크 세팅부터 차례대로 진행 하고, 서버를 리부팅 하면 설치는 완료입니다.

## DashBoard
!(/assets/TrueNAS/03. TrueNAS_Dashboard/TrueNAS_Dashboard 001.png)
설치가 완료된 TrueNAS의 메인화면입니다. 시스템의 상태를 한눈에 볼 수 있습니다.
시스템 관리자에게 필요한 정보를 직관적으로 제공해주고 있습니다.

## Storage / Dataset
이제 실제 사용할 스토리지 풀 및 데이터 셋을 만들어 보겠습니다.

!(/assets/TrueNAS/04. TrueNAS_Pool&Dataset/TrueNAS_Pool&Dataset_000.png)
먼저 풀을 생성합니다.

!(/assets/TrueNAS/04. TrueNAS_Pool&Dataset/TrueNAS_Pool&Dataset_001.png)
생성된 풀 ‘vg’ 의 우측의 메뉴를 열어 Add Dataset 을 실행합니다.

!(/assets/TrueNAS/04. TrueNAS_Pool&Dataset/TrueNAS_Pool&Dataset_003.png)
목적에 맞게 비어있는 필드를 채워줍니다.

!(/assets/TrueNAS/04. TrueNAS_Pool&Dataset/TrueNAS_Pool&Dataset_005.png)
이제 Share로 이동, Windows (SMB) Shares 에서 Add를 눌러 CIFS/SMB 공유를 만들어 줘야 합니다.

## ACL
그룹별 / 사용자별 권한을 제어해보겠습니다.
우선 시나리오는 아래와 같습니다.
개발팀(DEV) / 영업팀(SALE) / 기술팀(TECH) 세가지 부서가 있으며, 세 부서의 전용폴더를 각각 생성 및 타 부서의 전용폴더는 접속이 불가능 합니다.

!(/assets/TrueNAS/05. TrueNAS_User_Group/TrueNAS_User_Group_001.png)
저는 DEV / SALE / TECH 그룹을 만들었습니다.

!(/assets/TrueNAS/05. TrueNAS_User_Group/TrueNAS_User_Group_002.png)
SALE1 / SALE2 / DEV1 / DEV2 / TECH1 / TECH2 유저도 생성하였습니다.

!(/assets/TrueNAS/05. TrueNAS_User_Group/TrueNAS_User_Group_003.png)
유저를 생성할 때 원하는 그룹에 종속되게 할 수 있습니다.

!(/assets/TrueNAS/05. TrueNAS_User_Group/TrueNAS_User_Group_004.png)

!(/assets/TrueNAS/05. TrueNAS_User_Group/TrueNAS_User_Group_005.png)
물론 모든 유저를 다 만든 후, 그룹속성에서 원하는 유저를 넣는것도 됩니다.

## SMB / CIFS
이제 윈도우 시스템에서 SMB를 통해 공유폴더에 접속해보겠습니다.

!(/assets/TrueNAS/06. TrueNAS_SHARE/TrueNAS_Share_003.png)
그전에 ACL ( 계정 컨트롤 ) 을 진행해야 합니다.
생성한 Dataset 에서 View Permissions 로 들어갑니다.

!(/assets/TrueNAS/06. TrueNAS_SHARE/TrueNAS_Share_004.png)
연필 모양으로 된 Edit 버튼을 눌러줍니다.

!(/assets/TrueNAS/06. TrueNAS_SHARE/TrueNAS_Share_005.png)

!(/assets/TrueNAS/06. TrueNAS_SHARE/TrueNAS_Share_007.png)
Add Item 을 선택하여 만들어 두었던 그룹 또는 유저를 추가합니다.

!(/assets/TrueNAS/06. TrueNAS_SHARE/TrueNAS_Share_008.png)

!(/assets/TrueNAS/06. TrueNAS_SHARE/TrueNAS_Share_009.png)

!(/assets/TrueNAS/06. TrueNAS_SHARE/TrueNAS_Share_010.png)
권한을 제대로 설정 했다면, 각 부서별 전용폴더를 만들 수 있습니다.

## NFS MOUNT
이제 리눅스 시스템에서 마운트를 해보겠습니다.

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
마운트 후, 폴더가 생성되는지 시도 해봅니다.

!(/assets/TrueNAS/07. TrueNAS_NFS_MOUNT/TrueNAS_NFS_MOUNT_003.png)
윈도우 SMB 에서도 방금 생성한 new_folder 가 잘 보이는군요.

## Virtual Machines
TrueNAS는 VMware와 같은 가상화 PC 기능을 지원하고 있습니다.

!(/assets/TrueNAS/08. TrueNAS_Virtual Machines/TrueNAS_Virtual Machines_001.png)
VM 생성을 해보겠습니다.

!(/assets/TrueNAS/08. TrueNAS_Virtual Machines/TrueNAS_Virtual Machines_002.png)
순서는 VMware 등, 가상화 어플리케이션과 크게 다르지 않습니다.

!(/assets/TrueNAS/08. TrueNAS_Virtual Machines/TrueNAS_Virtual Machines_003.png)

!(/assets/TrueNAS/08. TrueNAS_Virtual Machines/TrueNAS_Virtual Machines_004.png)

!(/assets/TrueNAS/08. TrueNAS_Virtual Machines/TrueNAS_Virtual Machines_005.png)

!(/assets/TrueNAS/08. TrueNAS_Virtual Machines/TrueNAS_Virtual Machines_006.png)
미리 서버에 업로드 해두었던 ISO를 바로 불러와 OS 설치도 가능합니다.

!(/assets/TrueNAS/08. TrueNAS_Virtual Machines/TrueNAS_Virtual Machines_007.png)

!(/assets/TrueNAS/08. TrueNAS_Virtual Machines/TrueNAS_Virtual Machines_008.png)
생성이 완료된 VM의 모습입니다.

이 포스팅에서 다루지는 않았지만, Docker와 써드파티 플러그인등도 지원하고 있어 고성능 고사양 고용량의 데이터서버에 TrueNAS를 설치한다면 다재다능 다목적 서버로 사용하기에 손색이 없다고 할 수 있습니다.
