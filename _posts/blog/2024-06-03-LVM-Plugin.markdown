---
layout:     post
title:      "LVM 스냅샷 관리 기능 개발 후기 (1)"
date:       2024-06-03
author:     이헌제 (lhj4125@gluesys.com)
categories: blog
tags:       [스냅샷, 스토리지, LVM, Thin Provisioning, 장애, Storage, Metadata, 디스크 덤프]
cover:      "/assets/Snapshot1intro_maincover.png"
main:       "/assets/Snapshot1intro_maincover.png"
---

장애 복구나 유실된 데이터 복원을 위해서 AnyStor는 이전부터 스냅샷 기능을 지원하였습니다. 그러나 스냅샷 생성과 확인은 가능할 뿐, 실제로 복원 등에 사용하기 위해서는 관리자가 CLI 명령어를 사용하여 데이터를 복원할 수밖에 없었습니다. 실제 복원 시에는 고객 서비스에 영향이 없도록 진행되어야 했기에 도입하기 까다로웠던 점도 있었습니다. 이번에 스냅샷 기능을 재편하게 되었는데, 스냅샷을 안정적으로 도입하기 위해서 거쳤던 테스트와 이슈 대응 방안에 대해서 살펴보겠습니다.

&nbsp;

### 배경 설명

본 제품에서는 LVM 볼륨을 주로 다룹니다. LVM 볼륨의 프로비저닝 정책에 따라서 스냅샷의 종류도 나뉘게 되는데, 우선 볼륨의 프로비저닝 종류에 대해서 간략히 설명해 보겠습니다.

* **씬 프로비저닝(Thin Provisioning)된 볼륨** : 사용자에게 필요한 만큼의 스토리지 공간을 할당하되, 실제로는 사용한 만큼의 공간만 실제 스토리지에서 차지하는 방식입니다.

* **씩 프로비저닝(Thick Provisioning)된 볼륨** : 미리 정해진 크기의 스토리지 공간을 사용자에게 할당하는 방식입니다. 이 공간은 사용자가 실제로 사용하지 않더라도 할당된 크기만큼 스토리지에서 차지합니다. 스토리지 공간을 확보하는 데 있어서 보다 안정적이지만, 사용하지 않는 공간이 발생할 수 있어 스토리지 공간의 사용이 비효율적일 수 있습니다.

프로비저닝 된 볼륨에 따라서 스냅샷의 저장 방식도 바뀝니다. 

> 씬 프로비저닝된 볼륨과 씩 프로비저닝된 볼륨에 대해서 약칭으로 각각 Thin 볼륨, Thick 볼륨으로 변경하여 설명하겠습니다.

* **Thin 볼륨의 스냅샷**: 원본 볼륨의 데이터를 공유하며, 자체 메타데이터 영역을 가지고 있습니다. 메타데이터 영역에는 스냅샷의 논리적 익스텐트와 물리적 익스텐트 간의 매핑이 저장되어 있습니다. 이를 통해 스냅샷은 원본 볼륨의 상태를 보존하고, 변경 사항을 추적하게 됩니다.

* **Thick 볼륨의 스냅샷** : 원본 볼륨의 데이터를 복사하여 새로운 공간에 저장합니다. 원본 데이터의 완전한 복사본을 제공하지만, 스토리지 공간을 더 많이 차지하게 됩니다. 

여기까지만 살펴봤을 때 차이점이 여럿 보입니다. Thin 볼륨은 저장 방식이 다르기 때문에, 스냅샷 또한 저장하는 방법이 다르게 보입니다. 실제로 Thin 볼륨은 스냅샷을 다음과 같은 구조로 저장합니다. 

&nbsp;

> :bulb: NOTE <br>
> 물리적 익스텐트(Physical Extents: PE): 디스크의 섹터로 매핑된 물리적 할당 단위<br>
> 논리적 익스텐트(Logical Extents: LE): 물리적 익스텐트로 매핑된 논리적 할당 단위

&nbsp;


![Thin 볼륨 구조](/assets/Snapshot1intro_maincover.png){: width="700"}
<center>&#60; Thin 볼륨 구조 &#62;</center>

&nbsp;


위 구조를 보게 되면 Thin 볼륨과 스냅샷 볼륨은 공통의 데이터 볼륨을 공유합니다. 그렇기 때문에 많은 스냅샷을 생성할 수 있지만, 스냅샷을 삭제하더라도 여유 공간이 추가로 확보되지 않을 수도 있습니다. 데이터 볼륨 말고도 메타데이터 볼륨도 보이는데, 메타데이터 볼륨에서는 각 Thin 볼륨에 속한 데이터 볼륨을 추적합니다. 볼륨 그룹 별로 여러 씬 풀(Thin Pool)이 생성 될 수 있는데, 예비 메타데이터로 불리는`pmspare` 는 볼륨 그룹에 대해서 하나만 생성됩니다. 이 pmspare 는 볼륨 그룹 내의 모든 씬 풀(Thin Pool)의 메타데이터를 복구하기 위해서 사용됩니다.

> 씬 풀(Thin Pool) 은 약칭으로 Thin 풀로 변경하여 설명하겠습니다.

&nbsp;

### 스냅샷 도입 전 테스트


스냅샷을 도입하기 전에 몇 가지 스냅샷 기능에 관한 테스트를 진행하였습니다. 진행하면서 있었던 고려 사항들을 공유드리고자 합니다.

&nbsp;

#### 1. Thin 풀 데이터 볼륨 저장 공간 확보 

Thin 볼륨의 파일 시스템에서 파일을 삭제하면 일반적으로 씬 풀에 Free 블록을 다시 추가하지 않습니다. 파일 시스템에서는 삭제되었지만, 씬 풀에 적용되지 않은 경우, `fstrim` 을 통해서 물리적 공간을 Thin 풀에 복원할 수 있습니다. 비슷한 효과를 마운트 시에 옵션으로 처리할 수도 있는데, 마운트시에 `discard` 옵션으로 Thin 풀의 데이터 공간에 대한 자동 해제 옵션을 추가하여 데이터 볼륨의 저장 공간을 확보할 수 있었습니다.

&nbsp;

```bash
# Thin 볼륨 데이터 쌓기
dd if=/dev/zero of=/{mount_path}/fileN bs=4096 count=1000000;

# 용량 확인 
lvs
  LV           VG        Attr       LSize   Pool         Origin Data%  Meta%  Move Log Cpy%Sync Convert
  root         anystor-e -wi-ao---- <44.00g                      
  swap         anystor-e -wi-ao----   5.00g                          
  ThinLV       thinvpool Vwi-aotz--  60.00g tp_thinvpool        58.33  
  tp_thinvpool thinvpool twi---tz--  40.00g                     87.51  3.28 

# 데이터 삭제 후 재 마운트
# mount 시에 `-o discard` 추가
mount -o discard /dev/mapper/thinvpool-ThinLV /{mount_path}

# Thin 볼륨 데이터 쌓기
dd if=/dev/zero of=/{mount_path}/fileN bs=4096 count=1000000;

# 용량 확인
lvs
  LV           VG        Attr       LSize   Pool         Origin Data%  Meta%  Move Log Cpy%Sync Convert
  root         anystor-e -wi-ao---- <44.00g                                
  swap         anystor-e -wi-ao----   5.00g                                      
  ThinLV       thinvpool Vwi-aotz--  60.00g tp_thinvpool        1.78             
  tp_thinvpool thinvpool twi---tz--  40.00g                     2.67   1.64 
```

&nbsp;

#### 2. Thin 데이터 볼륨 공간 부족 

자동 확장을 설정한 경우 데이터 공간이 부족해지기 전에 설정값에 따라서 씬 풀의 데이터 공간이 확장됩니다. 하지만 확장할 공간이 없고 씬 풀의 데이터 공간이 이미 100%인 경우에도 추가로 디스크를 증설해 준다면 이후에 수동으로 확장할 수 있습니다. 만약 자동 확장 시 볼륨의 물리적인 용량이 부족한 경우 확장에 실패하여 데이터 볼륨이 가득 차게 되는 경우가 있는데, 그 경우의 쓰기 동작을 설정할 수 있습니다. 

데이터 볼륨에 여유 공간이 없는 경우, 큐 버퍼에 쓰기 명령을 넣었다가 확장이 완료되면 버퍼를 사용합니다. 기본 타임아웃(60초)이 지난 경우에는, 모든 쓰기 명령이 `error` 를 반환하게 됩니다. Thin 풀에서는 `--errorwhenfull` 옵션으로 Thin 풀이 가득 찼을 때, 큐 버퍼 사용 유무를 지정할 수 있습니다.  

&nbsp;

```bash
# Thin 풀의 데이터 볼륨이 가득 찬 경우
lvs
  LV           VG        Attr       LSize   Pool         Origin Data%  Meta%  Move Log Cpy%Sync Convert
  root         anystor-e -wi-ao---- <44.00g          
  swap         anystor-e -wi-ao----   5.00g           
  ThinLV       thinvpool Vwi-aotz--  60.00g tp_thinvpool        66.67   
  tp_thinvpool thinvpool twi---tzD-  40.00g                     100.00 3.53 

# Thin 풀의 errorwhenfull 옵션으로 파일 시스템의 동작 결정
lvchange --errorwhenfull (y/n) thinvpool/tp_thinvpool
```

&nbsp;

Thin 풀이 가득 찼을 때 파일 시스템의 동작을 결정했다면, 다음으로는 Thin 풀의 수동 확장으로 용량을 확장할 수 있습니다. Thin 풀만 확장해 준다면, Thin 볼륨은 자동으로 확장됩니다. 

&nbsp;

```bash
lvextend -L+{size} thinvpool/tp_thinvpool
```

&nbsp;

#### 3. Thin 풀 메타데이터 볼륨 공간 부족 


Thin 풀 메타데이터의 볼륨이 작고, 스냅샷이 많은 경우 메타데이터 볼륨이 부족할 수 있습니다. 만약 Thin 풀 메타데이터의 볼륨이 가득 찬 경우 메타데이터의 볼륨이 손상될 수 있습니다. 

&nbsp;

```bash
lvcreate -s -n snap1 vg1/thinvol
...
lvcreate -s -n snap600 vg1/thinvol

lvs                                         
  thinvol       vg1 Vwi-aotz--  10.00g tp_thinpool        82.70       
  tp_thinpool   vg1 twi-aotzM-  10.00g                    84.81  100.00                          
```

메타데이터를 확인하고 복구하는 것은 파일 시스템에서 `fsck/repair` 를 실행하는 것과 유사합니다.  Thin 풀의 메타데이터를 복구하는 방법 중 하나는 `lvconvert --repair {vg}/{thinpool}`  를 실행하는 것입니다, 이 동작에서는 pmspare 로 복구 메타데이터를 생성하고, 메타데이터를 교체할 수 있도록 유도합니다. 

단순히 공간이 더 필요한 경우는 메타데이터 확장을 시도해 볼 수 있습니다.

&nbsp;

```bash
#lvs -a
  LV                 VG Attr       LSize   Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert

  thinlv             vg Vwi-aotz--  10.00g thinpool     82.70                
  thinpool           vg twi-aotzM-  10.00g              84.81  100.00        
  [thinpool_tdata]   vg Twi-ao----  10.00g                                   
  [thinpool_tmeta]   vg ewi-ao----  12.00m  

#lvextend --poolmetadatasize +{size} vg/thinpool 

#lvs -a
   LV                VG Attr       LSize   Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert

  thinlv             vg Vwi-aotz--  10.00g thinpool     82.70                
  thinpool           vg twi-aotz--  10.00g              84.84  28.04         
  [thinpool_tdata]   vg Twi-ao----  10.00g                                   
  [thinpool_tmeta]   vg ewi-ao----  60.00m   
```

&nbsp;

#### 4. 메타데이터 장애 복구

실제 이용 시에는 메타데이터의 용량이 가득 찬 경우나, 디스크 장애 등의 사례에서 메타데이터가 손실되는 경우도 있었습니다. LVM 에서는 각각의 디스크가 동일한 볼륨 풀을 사용하고 있다면, 동일한 메타데이터를 디스크에 복사하여 사용하기 때문에, 디스크에 할당된 정보(PV 정보 등)을 제외하고 복사한다면 손쉽게 복구할 수 있습니다. 메타데이터 영역 중 디스크 정보에 해당하는 656Byte를 제외하고 1024KB까지 복사하여 손상된 디스크의 메타데이터를 복구합니다.

&nbsp;

```bash
# 메타데이터 장애 로그
  Metadata location on /dev/sde at 109056 begins with invalid VG name.
  Failed to read metadata summary from /dev/sde
  Failed to scan VG from /dev/sde
  Couldn't find device with uuid 3C36Fc-B9Fc-7LGH-EoAO-0r2c-ECrl-GuWorB.
  Cannot restore Volume Group VGPB with 1 PVs marked as missing.
  Restore failed.

# 임시 파일 복사 (백업용)
dd if=/dev/sde of=/root/temp bs=1020k count=1

# LVM 메타데이터 복사
dd if=/dev/sdd of=/dev/sde bs=1020k count=1 conv=notrunc

# LVM PV Header만 다시 복사
dd if=/root/temp of=/dev/sde bs=656 count=1 conv=notrunc
```

&nbsp;

LVM 메타데이터에서는 어떤 데이터가 있는지 확인한다면, 조금 더 세부적인 이슈에 대응할 수도 있습니다. 한번 메타데이터에 대해서도 자세하게 살펴보겠습니다.

&nbsp;

### LVM 의 메타데이터

[4. 메타데이터 장애 복구](#### 4. 메타데이터 장애 복구) 에서도 한 번 언급했던 LVM 의 메타데이터는 같은 볼륨 그룹 안의 물리 볼륨에 동일하게 저장되어 있습니다. 이번 장에서는 LVM 메타데이터가 어떻게 저장되어 있는지 [LVM2의 소스코드](https://github.com/lvmteam/lvm2)와 디스크 덤프를 비교하면서 상세하게 살펴보겠습니다.

우선 덤프를 위해 샘플 메타데이터부터 위 글과 같이 `/dev/sdd`, `/dev/sde` 의 물리 볼륨을 가지는 볼륨 그룹 `thick` 과 논리 볼륨 `thick_vol`, 스냅샷 `thick_snap` 으로 구성해 보겠습니다.

&nbsp;

```bash
# pvs
  PV         VG        Fmt  Attr PSize   PFree
  /dev/sdd   thick     lvm2 a--  <50.00g  48.98g
  /dev/sde   thick     lvm2 a--  <50.00g <50.00g

# vgs
  VG        #PV #LV #SN Attr   VSize  VFree
  thick       2   2   1 wz--n- 99.99g 98.98g

# lvs
  LV         VG        Attr       LSize  Pool Origin    Data%  Meta%  Move Log Cpy%Sync Convert
  thick_snap thick     swi-a-s--- 12.00m      thick_vol 0.00
  thick_vol  thick     owi-a-s---  1.00g
```

&nbsp;

우선 디스크 덤프 후 보기 편하게 16진수로 변경한 다음 전체 구성을 한번 살펴보겠습니다.

&nbsp;

```bash
# cat sdd_hex

...
0000200: 4c41 4245 4c4f 4e45 0100 0000 0000 0000  LABELONE........
0000210: a982 7799 2000 0000 4c56 4d32 2030 3031  ..w. ...LVM2 001
0000220: 4a6f 6c4f 5177 7833 4466 5033 756a 6e75  JolOQwx3DfP3ujnu
0000230: 776e 6435 4342 4735 6230 6747 5975 3874  wnd5CBG5b0gGYu8t
0000240: 0000 0080 0c00 0000 0000 1000 0000 0000  ................ 
0000250: 0000 0000 0000 0000 0000 0000 0000 0000  ................
0000260: 0000 0000 0000 0000 0010 0000 0000 0000  ................
0000270: 00f0 0f00 0000 0000 0000 0000 0000 0000  ................
0000280: 0000 0000 0000 0000 0200 0000 0100 0000  ................
0000290: 0000 0000 0000 0000 0000 0000 0000 0000  ................

...

0001000: 2af4 634e 204c 564d 3220 785b 3541 2572  *.cN LVM2 x[5A%r
0001010: 304e 2a3e 0100 0000 0010 0000 0000 0000  0N*>............
0001020: 00f0 0f00 0000 0000 00a0 0100 0000 0000  ................
0001030: 0007 0000 0000 0000 a181 917c 0000 0000  ...........|....
0001040: 0000 0000 0000 0000 0000 0000 0000 0000  ................
0001050: 0000 0000 0000 0000 0000 0000 0000 0000  ................
0001060: 0000 0000 0000 0000 0000 0000 0000 0000  ................
0001070: 0000 0000 0000 0000 0000 0000 0000 0000  ................
0001080: 0000 0000 0000 0000 0000 0000 0000 0000  ................

...

001b000: 7468 6963 6b20 7b0a 6964 203d 2022 3266  thick {.id = "2f
001b010: 7559 4431 2d48 5856 792d 315a 3275 2d76  uYD1-HXVy-1Z2u-v
001b020: 797a 332d 7765 4530 2d6c 6553 4a2d 716e  yz3-weE0-leSJ-qn
001b030: 6d79 784f 220a 7365 716e 6f20 3d20 3333  myxO".seqno = 33
001b040: 0a66 6f72 6d61 7420 3d20 226c 766d 3222  .format = "lvm2"
001b050: 0a73 7461 7475 7320 3d20 5b22 5245 5349  .status = ["RESI
001b060: 5a45 4142 4c45 222c 2022 5245 4144 222c  ZEABLE", "READ",
001b070: 2022 5752 4954 4522 5d0a 666c 6167 7320   "WRITE"].flags.
001b080: 3d20 5b5d 0a65 7874 656e 745f 7369 7a65  = [].extent_size

...
```

&nbsp;

메타데이터 정보가 여러 군데로 나눠서 저장되어 있는데, 크게 보자면 다음과 같이 구성되어 있는 것을 알 수 있습니다. 

&nbsp;

![디스크 덤프로 살펴보는 메타데이터의 구조](/assets/lvm_metadata1.png){: width="700"}
<center>&#60; 디스크 덤프로 살펴보는 메타데이터의 구조 &#62;</center>

&nbsp;

가장 처음 부분부터 소스코드와 함께 살펴볼까요?

&nbsp;

```c
0000200: 4c41 4245 4c4f 4e45 0100 0000 0000 0000  LABELONE........
0000210: a982 7799 2000 0000 4c56 4d32 2030 3031  ..w. ...LVM2 001

# cat lib/label/label.h

35 /* On disk - 32 bytes */
36 struct label_header {
37	int8_t id[8];		/* LABELONE */
38	uint64_t sector_xl;	/* Sector number of this label */
39	uint32_t crc_xl;	/* From next field to end of sector */
40	uint32_t offset_xl;	/* Offset from start of struct to contents */
41	int8_t type[8];		/* LVM2 001 */
42 } __attribute__ ((packed));
```

&nbsp;

맨 처음 부분은 **Label Header** 입니다. **Label Header** 에서는 다음과 같은 정보를 정의합니다.

&nbsp;

![Label Header](/assets/lvm_metadata_label.png){: width="700"}
<center>&#60; Label Header &#62;</center>

&nbsp;

LVM 이 사용하는 디스크라고 설명해 주며 정보가 어디까지 저장되어 있는지 설명해 주는 라벨이라고 말할 수 있습니다.

다음은 **PV Header** 입니다. **PV Header** 에서는 다음과 같은 정보를 정의합니다.


&nbsp;

```c
0000220: 4a6f 6c4f 5177 7833 4466 5033 756a 6e75  JolOQwx3DfP3ujnu
0000230: 776e 6435 4342 4735 6230 6747 5975 3874  wnd5CBG5b0gGYu8t
0000240: 0000 0080 0c00 0000 0000 1000 0000 0000  ................ 
0000250: 0000 0000 0000 0000 0000 0000 0000 0000  ................
0000260: 0000 0000 0000 0000 0010 0000 0000 0000  ................
0000270: 00f0 0f00 0000 0000 0000 0000 0000 0000  ................
0000280: 0000 0000 0000 0000 0200 0000 0100 0000  ................
0000290: 0000 0000 0000 0000 0000 0000 0000 0000  ................

# cat lib/format_text/layout.h

40 /* Fields with the suffix _xl should be xlate'd wherever they appear */
41 /* On disk */
42 struct pv_header {
43 	int8_t pv_uuid[ID_LEN];	/* 32 Byte */
44
45 	/* This size can be overridden if PV belongs to a VG */
46 	uint64_t device_size_xl;	/* Bytes */
47
48 	/* NULL-terminated list of data areas followed by */
49 	/* NULL-terminated list of metadata area headers */
50 	struct disk_locn disk_areas_xl[0];	/* Two lists */
51 } __attribute__ ((packed));

# cat lib/format_text/format-text.h

67 /* On disk */
68 struct disk_locn {
69 	uint64_t offset;	/* Offset in bytes to start sector */
70 	uint64_t size;		/* Bytes */
71 } __attribute__ ((packed));
```

&nbsp;

비트단위로 저장되어 있어 일일이 의미를 파악하기 어려울 수도 있는데, **PV Header** 에서는 다음과 같은 정보를 포함하고 있습니다.

&nbsp;

![PV Header](/assets/lvm_metadata_pv.png){: width="700"}
<center>&#60; PV Header &#62;</center>

&nbsp;

디스크에 정의된 PV 를 식별하기 위한 정보와 그 외 메타데이터의 정보의 위치를 저장하고 있습니다. 위 설명을 토대로 메타데이터의 헤더 영역 정보를 계산해 보자면, 초록색으로 시작점을 알리는 offset, 과 그 길이인 size 를 확인할 수 있습니다.

* **Metadata Header Offset** : `0010 0000 0000 0000`
* **Metadata Header Size** : `00f0 0f00 0000 0000`

&nbsp;

> :bulb: NOTE <br>
> bswap 을 사용하여 데이터를 저장하고 읽는 경우가 있습니다. 이는 byte 단위로 swap 해서 읽고 쓸 수 있는데, 예를 들어 metadata header offset 의 경우 `x0000 0000 0000 1000` 로 해석할 수 있습니다. 

&nbsp;

이제 **Metadata Header** 를 살펴보겠습니다.

&nbsp;

```c
0001000: 2af4 634e 204c 564d 3220 785b 3541 2572  *.cN LVM2 x[5A%r
0001010: 304e 2a3e 0100 0000 0010 0000 0000 0000  0N*>............
0001020: 00f0 0f00 0000 0000 00a0 0100 0000 0000  ................
0001030: 0007 0000 0000 0000 a181 917c 0000 0000  ...........|....
0001040: 0000 0000 0000 0000 0000 0000 0000 0000  ................
0001050: 0000 0000 0000 0000 0000 0000 0000 0000  ................
0001060: 0000 0000 0000 0000 0000 0000 0000 0000  ................
0001070: 0000 0000 0000 0000 0000 0000 0000 0000  ................
0001080: 0000 0000 0000 0000 0000 0000 0000 0000  ................

# cat lib/format_text/layout.h

 71 /* On disk */
 72 /* Structure size limited to one sector */
 73 struct mda_header {
 74		uint32_t checksum_xl;	/* Checksum of rest of mda_header */
 75		int8_t magic[16];	/* To aid scans for metadata */
 76		uint32_t version;
 77		uint64_t start;		/* Absolute start byte of mda_header */
 78		uint64_t size;		/* Size of metadata area */
 79
 80 	struct raw_locn raw_locns[0];	/* NULL-terminated list */
 81 } __attribute__ ((packed));

 60 /* On disk */
 61 struct raw_locn {
 62 	uint64_t offset;	/* Offset in bytes to start sector */
 63 	uint64_t size;		/* Bytes */
 64 	uint32_t checksum;
 65 	uint32_t flags;
 66 } __attribute__ ((packed));
```

&nbsp;

**Metadata Header** 에서는 다음과 같은 정보를 포함하고 있습니다.

&nbsp;

![Metadata Header](/assets/lvm_metadata_metadata.png){: width="700"}
<center>&#60; Metadata Header &#62;</center>

&nbsp;

이제 앞서 **PV Header** 에서 **Metadata Header** 의 저장된 위치를 계산했던 것처럼, **Metadata** 의 위치를 이제 간단하게 계산해 볼 수 있습니다.

* **Metadata Offset** : `x1000 + x1a000 = x1b000`

&nbsp;

```c
001b000: 7468 6963 6b20 7b0a 6964 203d 2022 3266  thick {.id = "2f
001b010: 7559 4431 2d48 5856 792d 315a 3275 2d76  uYD1-HXVy-1Z2u-v
001b020: 797a 332d 7765 4530 2d6c 6553 4a2d 716e  yz3-weE0-leSJ-qn
001b030: 6d79 784f 220a 7365 716e 6f20 3d20 3333  myxO".seqno = 33
001b040: 0a66 6f72 6d61 7420 3d20 226c 766d 3222  .format = "lvm2"
001b050: 0a73 7461 7475 7320 3d20 5b22 5245 5349  .status = ["RESI
001b060: 5a45 4142 4c45 222c 2022 5245 4144 222c  ZEABLE", "READ",
001b070: 2022 5752 4954 4522 5d0a 666c 6167 7320   "WRITE"].flags.
001b080: 3d20 5b5d 0a65 7874 656e 745f 7369 7a65  = [].extent_size
```

&nbsp;

실제 메타데이터에서는 볼륨 그룹 객체를 기반으로 PV 정보와 LV 정보를 정의하여 LVM 을 관리하고 있었습니다. Thin 볼륨과 Thick 볼륨은 다음과 같이 메타데이터의 형태가 다릅니다. 메타데이터를 통해서 Thin 볼륨은 Thin 풀에서 정의되어 있는 PV 의 데이터를 활용할 수 있습니다.

&nbsp;

![Metadata](/assets/lvm_metadata2.png){: width="700"}
<center>&#60; Thin, Thick 볼륨의 Metadata &#62;</center>

&nbsp;

### 마치며

이 외에도 스냅샷 서비스의 스펙을 결정하기 위해서 많은 고민이 있었고, 또 고도화를 위해서 많은 의견들이 있었습니다. 예를 들어 섀도 복제본(Shadow copy)을 통한 스냅샷의 Windows 클라이언트 노출, Gluster 볼륨의 스냅샷 제공, PV 의 메타데이터가 너무 작은 경우 스냅샷 생성 실패 사례, 여러 가지 장애 케이스(Thin 볼륨, 파일 시스템, PV, VG, Data LV 등의 각각의 장애 사례)에 대한 위험 관리의 다양한 측면으로 서비스를 더욱더 안정적으로 확장해 가도록 진행하고 있습니다.

&nbsp;

### 참고

* [lvmthin linux manual page](https://man7.org/linux/man-pages/man7/lvmthin.7.html)

### LVM 글 더보기

* [LVM Basic Architecture](https://tech.gluesys.com/blog/2019/04/08/LVM.html)
* [LVM 스냅샷 관리 기능 개발 후기 (1)](https://tech.gluesys.com/blog/2024/06/03/LVM-Plugin.html)
