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
UPS(Uninterruptible Power Supply)가 불안정한 상태에서 전원 점검 작업 시에 후지쯔 스토리지의 컨트롤러에 일시적인 오류가 발생하였습니다.
후지쯔 스토리지가 일시적으로 다운되면서 NAS failover 과정 중 오류로 인하여 재부팅이 시작되었습니다.
재부팅 이후 Physical Volume이 정상적으로 인식되지 않아 missing 이 되었고 이에 대해 복구하는 방법 및 재현 방법을 공유하고자 합니다.

### 2. 상태 확인 및 해결 방법
이번 장애 상황은 Physical Volume 의 상태만 missing 상태이고 그 외에는 정상인 상태의 경우 입니다.
만약 위와 같이 특수한 상황에서의 장애가 아니라 실제로 metadata에 문제가 있다면 다른 방법을 통하여 복구해야 합니다.
Physical Volume이 누락되었는지 확인 작업이 필요합니다. 가장 간단한 방법은 pvs 명령어를 사용하여 attributes에 m 표시를 확인하는 방법이 있습니다.
```bash
pvs
```

![Alt text](/assets/pv_missing.PNG){: witdh="350"}

혹은 다른 방법으로 Volume Group에서 누락된 Physical Volume 을 몇개 인지 확인할 수 있습니다.
vgchange 명령에 v 옵션을 사용하면 실패 원인을 출력해줍니다. 이를 이용하여 Physical Volume이 누락된 정보 혹은 vgchange에 실패하는 다른 원인도 알 수 있습니다. 
```bash
vgchange -ay -v vg_name
```

![Alt text](/assets/vgchange_ay_v.PNG){: witdh="350"}

누락된 Physical Volume 을 확인하였으면 pvck 명령을 통하여 해당 Volume Group 이 정상 상태인지 확인해야 하는 작업이 필요합니다.
Physical Volume 의 상태를 확인할 수 있는 명령어인 pvck 명령을 사용하여 해당 Physical Volume 상태를 확인합니다.
pvck 이후 정상 여부를 확인하는 방법은 pvck 결과를 확인하는 방법도 있지만 pvck 명령이 정상 종료되었는지 echo $? 명령을 이용하여 확인할 수 있습니다.
```bash
pvck -v /dev/sdb
pvck -vvvv /dev/sdc
echo $?
```

![Alt text](/assets/pvck_echo.PNG){: witdh="350"}

위 명령어들을 통해 Physical Volume 가 정상 상태임을 확인했으면 Volume Group 에 추가해주는 작업이 필요합니다
vgextend 명령을 사용하여 missing 된 Physical Volume 을 Volume Group에 추가 해주도록 합니다.
위와는 다른 비정상 상황에는서 vgreduce --removemissing 명령을 사용하기도 하는데 데이터를 보존해야한다면 사용하면 안되는 명령입니다.
```bash
vgextend --restoremissing vg_name /dev/sdb
```

위 명령이 정상적으로 종료 되었다면 Physcal Volume, Volume Group, Losical Volume 의 상태를 각각 확인하도록 합니다.
```bash
pvs
vgs
lvs
```

### 3. pv 강제 missing 상태 만드는 법
보통 문제가 발생하면 그 문제에 대해 재현해서 검증하고 복구 혹은 패치하는 작업이 필요한 경우가 있다고 생각되어
재현 방법에 대해서도 공유합니다.
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

이후 vg_name.vg 파일에서 관련 pv의 flags = [] 부분에 MISSING 을 추가합니다.
```c
flags = ["MISSING"]
```

/etc/lvm/backup/vg_name 을 백업해두고 해당 파일을 수정해야합니다.
PV missing이 발생하면 자동으로 backup 파일을 찾기 때문에 해당 파일도 MISSING을 추가하거나 이동해야 합니다.
pv 강제 missing 상태로 변경하는 명령입니다.
```bash
vgcfgrestore vg_name -f vg_name.vg --force 
```

위 단계를 모두 마치면 pv가 일시적으로 missing 상태인 것을 확인할 수 있습니다.
- - -
참고
1. pvs http://man7.org/linux/man-pages/man8/pvs.8.html
2. vgs https://linux.die.net/man/8/vgs
3. lvs http://man7.org/linux/man-pages/man8/lvs.8.html
