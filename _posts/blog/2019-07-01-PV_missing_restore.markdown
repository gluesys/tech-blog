---
layout:     post
title:      "특수한 전원 장애 상황에서 PV missing 복구"
date:       2019-07-01 14:01:00
author:     권 진영 (gc757489@gmail.com)
categories: blog
tags:       PV, VG
cover:      "/assets/missing.PNG"
---

## 특수한 상황에서 발생한 PV missing 복구

### 1. 특수 상황의 전원 장애 발생
UPS(Uninterruptible Power Supply)가 불안정한 상태에서 전원 점검 작업 시에 스토리지의 컨트롤러에 일시적인 오류가 발생하였습니다.
후지쯔 스토리지가 일시적으로 다운되면서 NAS failover 과정 중 오류로 인하여 재부팅이 시작되었습니다.
재부팅 이후 글러스터 볼륨의 상태가 비정상 상태인 것을 인지하고 pacemaker 상태를 확인하니 Gluster Volume 및 Volume Group  Resource agent가 비정상상태였습니다.
Volume Group Resource agent 가 비정상 상태인 원인을 파악하던 중 Physical Volume 의 상태가 missing 인 것을 확인하였습니다.
재부팅 이후에 스토리지와 연결과정에서 차후 추가된 스토리지의 Physical Volume 에서만 missing 이 발생하였고
특수한 상황에서 비정상 종료된 스토리지가 늦게 연결되어서 발생한 문제로 생각됩니다.
이에 대해 복구하는 방법 및 재현 방법을 공유하고자 합니다.

### 2. 상태 확인 및 해결 방법
상황을 구체적으로 확인하기 위해서 처음으로 lvs, vgs, pvs 명령을 사용하였습니다
```bash
pvs
vgs
lvs
```
![Alt text](/assets/missing.PNG){: witdh="350"}
위 명령으로 확인했을 경우 누락된 PV에 연관되어 Volume Group 및 Logical Volume 이 partial 상태이고 Physical Volume 은 missing 임을 확인할 수 있습니다.
관련 정보를 좀더 얻기 위해서 vgs, pvs, pvscan 등의 명령에 v 옵션을 추가하여 실행하면 되는데 그 중 vgchange 명령을 사용하여 확인하였습니다.
```bash
pvs -v
vgs -v
pvscan -v
vgchange -ay -v
```
![Alt text](/assets/vgchange_ay_v.PNG){: witdh="350"}
위 명령을 사용하여 누락된 Physical Volume 들의 정보를 확인하였습니다.
v 옵션은 최대 vvvv 까지 사용하고 더 자세한 정보를 확인할 수 있습니다.
이후 Physical Volume 의 정상 상태를 확인하기 위하여 pvck 명령을 사용하였습니다.
```bash
pvck -v /dev/sdb
pvck -vvvv /dev/sdc
echo $?
```
![Alt text](/assets/pvck_echo.PNG){: witdh="350"}

pvck -v 명령을 사용하여 Physical Volume 의 상태를 확인하고 echo $? 명령을 사용하여 pvck 가 정상 종료 되었는지 확인할 수 있습니다.
이번 상황의 경우에는 Physical Volume 을 인식하는 과정에서 문제가 발생하였을 뿐 metadata, UUID 등의 정보는 정상인 상황이었습니다.
만약 pvck 명령 사용 후 metadata 등에 문제가 있다면 /etc/lvm/backup/vg_name 을 이용하여 복구하는 방법이 있습니다.
Physical Volume 가 정상 상태임을 확인했으면 Volume Group 에 추가해주는 작업이 필요합니다

vgextend 명령을 사용하여 missing 된 Physical Volume 을 Volume Group에 추가 해주도록 합니다.
```bash
vgextend --restoremissing vg_name /dev/sdb
```
Physical Volume이 비정상인  상황에서 vgreduce --removemissing 명령을 사용하기도 하는데 해당 명령을 사용하면 Volume Group 에서 missing 상태인 Physical Volume 을 제외합니다.
스토리지에서 데이터를 보존해야한다면 사용하면 안되는 명령입니다.
missing 상태인 Physical Volume 이 정상적으로 복구 되었다면 lvs, vgs, pvs 등의 명령어를 사용시 missing 및 partial 상태가 사라진 것을 확인할 수 있습니다.

### 3. pv 강제 missing 상태 만드는 법
보통 문제가 발생하면 그 문제에 대해 재현해서 검증하고 복구 혹은 패치하는 작업이 필요한 경우가 있다고 생각되어 재현 방법에 대해서도 공유합니다.
위 상황을 강제로 재현하기 위해서는 yumdownloader 혹은 https://vault.centos.org 를 통하여 LVM 소스코드를 다운 받습니다.
해당 LVM 코드의 lib/format_text/archiver.c 를 수정합니다

```c
if(missing_pvs == 0)
    r=backup_restor_vg(cmd, vg, NULL);   //하단부에
else if (missing_pvs < 4){               //추가   //만약 테스트할 vg가 4개 이상이라면 수정이 필요합니다.
    r = backup_restore_vg(cmd, vg, 0, NULL);
}
```
lib/metadata/metadata.c 의내용도 아래와 같이 수정합니다. 
```c
if (vg_missing_pv_count(vg) && !vg->cmd->handles_missing_pvs){     //vg->cmd->handles_missing_pvs 앞부분에 !를 추가합니다.
    log_error("Cannot update volume group %s while physical " 
            "volumes are missing.", vg->name);
    return 0;
}
```

위 파일 2개를 수정한 후 LVM rpmbuild 하여 업데이트하도록 합니다.
vgbackup 파일 생성 및 수정을 을해야 하는데 아래 명령을 사용하여 Volumge Group 의 백업 파일을 생성합니다
```bash
vgcfgbackup vg_name -f vg_name.vg
```

이후 vg_name.vg 파일에서 관련 Physical Volume 의 flags = [] 부분에 MISSING 을 추가합니다.
```c
flags = ["MISSING"]
```

/etc/lvm/backup/vg_name 을 백업해두고 해당 파일을 수정해야합니다.
PV missing이 발생하면 자동으로 backup 파일을 찾기 때문에 해당 파일도 MISSING을 추가하거나 이동해야 합니다.
pv 강제 missing 상태로 변경하는 명령입니다.
```bash
vgcfgrestore vg_name -f vg_name.vg --force 
```

위 단계를 모두 마치면 Physical Volume이 일시적으로 missing 상태인 것을 확인할 수 있습니다.

### 4. pvs, vgs, lvs 의 일부 Attributes 설명
#### pvs
##### normal status
feild 1 - (a)allocatable
##### abnormal or specific
field 1 - (d)uplicate : multipath로 구성된 디스크에서 path가 2개이상일 경우 LVM 에서 metadata에 대하여 중복된 데이터를 읽을 경우에 발생할 수 있습니다.
field 3 - (m)issing : 물리적 디스크가 제거되거나 /dev/sdx 를 지우거나 UUID, metadata가 잘못 매칭 되는 경우에 발생할 수 있습니다.
#### vgs
##### normal status
field 1 - (w)riteable
field 2 - resi(z)able
field 5 - (n)ormal
##### abnormal or specific
field 4 - (p)artial : 하나 이상의 물리 볼륨이 누락되었음을 나타냅니다.
#### lvs
##### normal status
field 2 - (w)riteable
field 3 - (i)nherited
field 5 - (a)ctive
field 6 - (o)pen
##### abnormal or specific
field 9 - (p)artial : 하나 이상의 물리 볼륨이 누락되었음을 나타냅니다.
- - -
참고
1. pvs http://man7.org/linux/man-pages/man8/pvs.8.html
2. vgs https://linux.die.net/man/8/vgs
3. lvs http://man7.org/linux/man-pages/man8/lvs.8.html
