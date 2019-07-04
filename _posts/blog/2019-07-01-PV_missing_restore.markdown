---
layout:     post
title:      "특수한 전원 장애 상황에서 PV missing 복구"
date:       2019-07-01 14:01:00
author:     권 진영 (gc757489@gmail.com)
categories: blog
tags:       PV, VG, LVM, Trouble shooting
cover:      "/assets/missing.PNG"
---

## 특수한 상황에서 발생한 PV missing 복구

### 1. 특수 상황의 전원 장애 발생

UPS(Uninterruptible Power Supply)가 불안정한 상태에서 전원 점검 작업 시에 스토리지의 컨트롤러에 일시적인 오류가 발생하였습니다.
후지쯔 스토리지가 일시적으로 다운되면서 NAS failover 과정 중 오류로 인하여 재부팅이 시작되었습니다.
재부팅 이후 글러스터 볼륨의 상태가 비정상 상태인 것을 인지하고 pacemaker 상태를 확인하니 글러스터 볼륨 및 볼륨 그룹(Volume Group, 이하 VG) Resourceagent가 비정상상태였습니다.
VG Resource agent가 비정상 상태인 원인을 파악하던 중 물리 볼륨(Physical Volume, 이하 PV)의 상태가 missing인 것을 확인하였습니다.
재부팅 이후에 스토리지와 연결 과정에서 차후 추가된 스토리지의 PV에서만 missing이 발생하였고
특수한 상황에서 비정상 종료된 스토리지가 늦게 연결되어서 발생한 문제로 생각되었습니다.
이에 대해 복구하는 방법 및 재현 방법을 공유하고자 합니다.

### 2. 상태 확인 및 해결 방법

상황을 구체적으로 확인하기 위해서 처음으로 `lvs, vgs, pvs` 명령을 사용하였습니다

```bash
pvs
vgs
lvs
```

![Alt text](/assets/missing.PNG){: width="900"}

위 명령으로 확인했을 경우 누락된 PV에 연관되어 VG 및 논리 볼륨(Logical Volume, 이하 LV)이 partial 상태이고 PV는 missing임을 확인할 수 있습니다.
관련 정보를 좀 더 얻기 위해서 `vgs, pvs, pvscan` 등의 명령에 `-v` 옵션을 추가하여 실행하면 되는데 그 중 `vgchange` 명령을 사용하여 확인하였습니다.

```bash
pvs -v
vgs -v
pvscan -v
vgchange -ay -v
```

![Alt text](/assets/vgchange_ay_v.PNG){: width="900"}

위 명령을 사용하여 누락된 PV들의 정보를 확인하였습니다.
`-v` 옵션은 사용 개수에 따라 더 상세한 정보를 출력할 수 있으며, 최대 4개까지 사용할 수 있습니다.
이후 PV의 정상 상태를 확인하기 위하여 `pvck` 명령을 사용하였습니다.

```bash
pvck -v <물리 볼륨 이름> 
pvck -vvvv <물리 볼륨 이름>
echo $?
```

![Alt text](/assets/pvck_echo.PNG){: width="900"}

`pvck -v` 명령을 사용하여 PV의 상태를 확인하고 `echo $?` 명령을 사용하여 `pvck` 결과가 정상 종료되었는지 확인할 수 있습니다.
이번 장애 상황에서는 PV를 인식하는 과정에서 문제가 발생하였을 뿐 LVM 메타데이터, UUID 등의 정보는 정상인 상황이었습니다.
만약 `pvck` 명령 사용 후 LVM 메타데이터 등에 문제가 있다면 `/etc/lvm/backup/<볼륨 그룹 이름>` 을 이용하여 복구하는 방법이 있습니다.
PV가 정상 상태임을 확인했으면 기존의 VG에 추가해주는 작업이 필요합니다

vgextend 명령을 사용하여 missing된 PV를 VG에 추가해 주도록 합니다.

```bash
vgextend --restoremissing <볼륨 그룹 이름> <물리 볼륨 이름>
```

PV가 비정상인 상황에서 vgreduce --removemissing 명령을 사용하기도 하는데, 해당 명령을 사용하면 VG에서 missing 상태인 PV를 제외합니다.
PV가 제외된다면 PV에 담겨 있던 데이터는 접근할 수 없게 되어 유실되기 때문에 스토리지에서 데이터를 보존해야 한다면 사용하면 안 되는 명령입니다.
missing 상태인 PV가 정상적으로 복구되었다면 lvs, vgs, pvs 등의 명령어를 사용할 때 missing 및 partial 상태가 사라진 것을 확인할 수 있습니다.

### 3. pv 강제 missing 상태 만드는 법

보통 문제가 발생하면 그 문제를 재현해서 검증하고 복구 혹은 patch를 위한 재현을 하는 경우가 있을 것이로 생각되어 재현 방법에 대해서도 공유합니다.
LVM에서는 위 상황을 강제로 재현할 수 있는 기능을 제공하지 않기 때문에 기존 LVM 코드를 수정할 필요가 있습니다.
yumdownloader 혹은 https://vault.centos.org 를 통하여 LVM 소스 코드를 다운로드받습니다.
첫 번째로 LVM 코드의 `lib/format_text/archiver.c`를 수정해야 합니다.
누락된 PV가 0개인 경우에만 `backup_restore_vg()`함수를 실행합니다.
`backup_restore_vg()`함수에서는 PV 익스텐트나 fid 등을 검사하는데 검사 후 정상일 경우에는 복구를 실행하고 정상이 아닐 경우 복구를 실행하지 않고 오류 메시지를 출력합니다.
누락된 PV 개수가 0개 이상일 경우에도 실행되야 하고 `backup_restore_vg()`함수에서 missing 상태임을 확인해야 강제로 PV missing 상태로 전환할 수 있습니다.

```c
if(missing_pvs == 0)
    r=backup_restore_vg(cmd, vg, NULL);   //하단부에
else if (missing_pvs < 4){                //추가   //만약 테스트할 vg가 4개 이상이라면 수정이 필요합니다.
    r = backup_restore_vg(cmd, vg, 0, NULL);
}
```

`lib/metadata/metadata.c` 파일도 아래와 같이 수정합니다. 
아랫부분은 `handles_missing_pvs` 값이 1로 고정된 부분입니다. 해당 부분을 0 으로 수정하여 missing된 개수와 다르게 변경하여 오류 출력 및 종료를 skip 할 수 있도록 하는 부분입니다.
해당 부분을 수정하기 위해서 `vg->cmd->handles_missing_pvs` 앞부분에 `"!"`를 추가합니다.
```c
if (vg_missing_pv_count(vg) && !vg->cmd->handles_missing_pvs){     //vg->cmd->handles_missing_pvs 앞부분에 "!"를 추가합니다.
    log_error("Cannot update Volume Group %s while physical " 
            "volumes are missing.", vg->name);
    return 0;
}
```

위 파일에서 2부분을 수정한 후 LVM RPM 패키지를 새로 빌드하도록 합니다.

```bash
rpmbuild -ba rpmbuild/SPECS/lvm2.spec

+ umask 022
+ cd /root/rpmbuild/BUILD
+ cd /root/rpmbuild/BUILD
+ rm -rf boom-0.9
+ /usr/bin/gzip -dc /root/rpmbuild/SOURCES/LVM2.2.02.180.tgz

...

Wrote: /root/rpmbuild/RPMS/x86_64/device-mapper-devel-1.02.149-8.el7.x86_64.rpm
Wrote: /root/rpmbuild/RPMS/x86_64/device-mapper-libs-1.02.149-8.el7.x86_64.rpm
Wrote: /root/rpmbuild/RPMS/x86_64/device-mapper-event-1.02.149-8.el7.x86_64.rpm
Wrote: /root/rpmbuild/RPMS/x86_64/device-mapper-event-libs-1.02.149-8.el7.x86_64.rpm
Wrote: /root/rpmbuild/RPMS/x86_64/device-mapper-event-devel-1.02.149-8.el7.x86_64.rpm
Wrote: /root/rpmbuild/RPMS/noarch/lvm2-python-boom-0.9-11.el7.noarch.rpm
Executing(%clean): /bin/sh -e /var/tmp/rpm-tmp.WCYNcY
+ umask 022
+ cd /root/rpmbuild/BUILD
+ cd LVM2.2.02.180
+ rm -rf /root/rpmbuild/BUILDROOT/lvm2-2.02.180-8.el7.x86_64
+ exit 0
```

rpmbuild 완료 후 특별한 오류가 출력이 되지 않는다면 정상 종료된 것을 확인할 수 있습니다.
이제 rpm 업그레이드를 사용하여 기존에 설치된 LVM 패키지를 대체합니다.

```bash
rpm -Uvh --force {lvm2-2*,lvm2-debuginfo*,lvm2-libs*,device-mapper*}
```

rpm 업그레이드를 완료하였다면 bakcup파일 을 수정하여 PV 상태를 변경시키도록 합니다. 
vgbackup 파일 생성 및 수정을 해야 하는데, 아래 명령을 사용하여 VG의 백업 파일을 생성합니다.

```bash
vgcfgbackup <볼륨 그룹 이름> -f <볼륨 그룹 이름>.vg
```

PV를 강제로 missing 상태로 만들기 위해서는 PV 상태를 수정해야 합니다.
`<볼륨 그룹 이름>.vg` 파일에서 관련 PV의 flags = [] 부분에 `"MISSING"`을 추가합니다.

```c
flags = ["MISSING"]
```

`/etc/lvm/backup/<볼륨 그룹 이름>` 을 백업해두고 해당 파일을 수정해야 합니다.
PV missing이 발생하면 자동으로 VG의 LVM 설정 백업 파일을 찾아서 복구하기 때문에 해당 파일도 `"MISSING"`을 추가하거나 이동해야 합니다.
PV를 강제로 missing 상태로 변경하는 명령입니다.

```bash
vgcfgrestore <볼륨 그룹 이름> -f <볼륨 그룹 이름>.vg --force 
```

위 단계를 모두 마치면 PV가 일시적으로 missing 상태인 것을 확인할 수 있습니다.

### 4. pvs, vgs, lvs 의 일부 Attributes 설명

#### pvs

| normal status               | description|
| :-------------------------: |-------------|
| feild 1 - (a)allocatable    | |

| abnormal or specific        | description|
| :-------------------------: |-------------|
| field 1 - (d)uplicate       | multipath로 구성된 디스크에서 path가 2개이상일 경우 LVM 에서 LVM 메타데이터에 대하여 중복된 데이터를 읽을 경우에 발생할 수 있습니다. |
| field 3 - (m)issing         | 물리적 디스크가 제거되거나 /dev/sdx 를 지우거나 UUID, LVM 메타데이터가 잘못 매칭 되는 경우에 발생할 수 있습니다. |

#### vgs

| normal status               | description|
| :-------------------------: |-------------|
| field 1 - (w)riteable       | |
| field 2 - resi(z)able       | |
| field 5 - (n)ormal          | |

| abnormal or specific        | description|
| :-------------------------: |-------------|
| field 4 - (p)artial         | 하나 이상의 PV가 누락되었음을 나타냅니다. |

#### lvs

| normal status               | description |
| :-------------------------: |-------------|
| field 2 - (w)riteable       | |
| field 3 - (i)nherited       | |
| field 5 - (a)ctive          | |
| field 6 - (o)pen            | |

| abnormal or specific        | description |
| :-------------------------: |-------------|
| field 9 - (p)artial         | 하나 이상의 PV가 누락되었음을 나타냅니다. |

- - -
참고
1. pvs http://man7.org/linux/man-pages/man8/pvs.8.html
2. vgs https://linux.die.net/man/8/vgs
3. lvs http://man7.org/linux/man-pages/man8/lvs.8.html
