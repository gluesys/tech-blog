---
layout:     post
title:      "NextCloud 개념잡기"
date:       2021-02-15 08:43:59
author:     이 태민 (tmlee@gluesys.com)
categories: blog
tags:      Cloud-오픈소스-클라우드-기능리뷰-스토리지-파일스토리지 
cover:      "/assets/IntelOptaneIMDT.png"
main:      "/assets/IntelOptaneIMDT_main.jpg"
---

====

1.NextCloud 란?
----
1. NextCloud는 파일 호스팅 서비스를 만들고 사용하기 위한 client-server software이며, 오픈소스로 알려진 인프라 구축을 진행함.

2. 개인 서버 장치에 설치하여 운영할 수 있고 Office , Google Drive , MatterMost , Calendar 통합된 기능이면서
로컬 컴퓨터 또는 외부 파일 스토리지 호스팅에 사용할 수 있어 NAS 기술을 접하는 사람으로써 Storage Cloud 서비스에 적합
하다고 판단하여 진행함.

3. 원래는 OwnCloud 개발자인 Frank Karlitschek은 OwnCloud에서 파생된 NextCloud를 만들었다.

4. 웹이나 앱에서 서버의 파일을 사용하고, 파일을 전송하고, 파일을 외부와 공유할 Url을 만든다.

5. 모바일 기기에서 촬영한 사진을 자동으로 업로드, WebDav 프로토콜과 채팅의 기능도 제공한다.

![Nextcloud](/assets/1.JPG)

2.NAS와Cloud의 조합
----

**NAS(Network Attach Storage)를 많은 사용자의 관점에서 단순히 백업용으로 생각하고 사용하고 있다. NAS는 파일 관리에 적합하여 
기능에 대표적인 하나로 클라우드 서비스도 제공을 한다.**
**Petabyte나 Exabyte 같은 단위가 이제는 기업에서 폭발적으로 사용하는 데이터 활용에 있어서 대응 및 서비스를 하기 위해
활용성이 떨어지는 데이터와 활용성이 높은 데이터를 분류할 수도 있습니다.**
**NAS는 '네트워크 드라이브'나 '외부 저장장치의' 형태로만 사용되고 Cloud 서비스를 이용하면 '동기화 방식'이 기본으로 되어
용량이 늘어나면서 NAS와 같이 활용되는 목적으로 구축된다고 합니다.**
**NAS는 하드디스크에 의존하고, Raid구성으로 비용도 많이 드는데, 클라우드 서비스는 휴지통이나 , 파일 히스토리 기능을 지원하여
복구가 수월하다고 생각되어 안정성이 보장된다고 생각이 된다.**

![NextCloud](/assets/2.JPG)

3.NextCloud 설치과정
----
* CentOS 7.9 , PHP7.2 , MariaDB 배포하고 Apache에서 실행되는 Nextcloud를 배포한다.
* CentOS 7 설치하여 성공적인 플랫폼을 제공하도록 구축 하였다.
<pre>
<code>
~]# yum update -y * 최신 커널 업데이트를 진행한다.
~]# yum install -y httpd * Apache 웹 서버 패키지를 설치한다.
</code>
</pre>

#### 3.1 Apache 설정 -> vim /etc/httpd/conf.d/nextcloud.conf
<pre>
<code>
<> -> {}로 표기
{VirtualHost *:80} 
  DocumentRoot /var/www/html  // 실제 소스파일이 있는 Web Root 지정소
  ServerName test.domain.com  // 서비스 할 도메인 지정소
{Directory "/var/www/html/"}
  Require all granted  // 디렉터리에 대한 액세스 허용
  AllowOverride All    // 접근자를 모두 허락하도록 설정
  Options FollowSymLinks MultiViews  // 디렉터리에 대한 특정 옵션 설정
{/Directory}
{/VirtualHost}
</code>
</pre>
~]# systemctl enable httpd.service

~]# systemctl start httpd.service
* Apache Web Service 데몬 enable과 start 시킨다.

#### 3.2 PHP 관련 패키지 설치
* NextCloud는 PHP 기반 프로그래밍 언어를 사용하여 새로운 모듈을 만들고 싶으면 (최신)7.2이상의 패키지를 설치한다.
<pre>
<code>
~]# yum install -y centos-release-scl
rh-php72 rh-php72-php rh-php72-php-gd rh-php72-php-mbstring \
rh-php72-php-intl rh-php72-php-pecl-apcu rh-php72-php-mysqlnd rh-php72-php-pecl-redis \
rh-php72-php-opcache rh-php72-php-imagick
</code>
</pre>

#### 3.3 Apache 설정 파일 SymLinks 
<pre>
<code>
~]# ln –s /opt/rh/httpd24/root/etc/httpd/conf.d/rh-php72-php.conf /etc/httpd/conf.d/
~]# ln -s /opt/rh/httpd24/root/etc/httpd/conf.modules.d/15-rh-php72-php.conf /etc/httpd/conf.modules.d/
~]# ln -s /opt/rh/httpd24/root/etc/httpd/modules/librh-php72-php7.so /etc/httpd/modules/
</code>
</pre>
* httpd 설치 경로 /opt/rh/httpd24에서 Nextcloud 설정 경로와 심볼릭 링크를 구성 하였다.

#### 3.4 MariaDB 설치
<pre>
<code>
~]# yum install -y mariadb mariadb-server
~]# systemctl enable mariadb.service
~]# systemctl start mariadb.service
</code>
</pre>
* 이 작업을 완료 한 후 Nextcloud가 액세스 할 수 있도록 사용자 이름과 비밀번호로 데이터 베이스를 생성합니다.

#### 3.5 Nextcloud 설치
1. [NextCloud Install](https://nextcloud.com/install/)
* NextCloud Server 다운로드 -> 다운로드 -> 서버 소유자 용 아카이브 파일로 이동하여 tar.bz2 다운로드 하였다. 
2. GPG-PUB-KEY Error로 인한 yum install 실패 조치 사항
<pre>
<code>
~]# wget https://download.nextcloud.com/server/release/nextcloud-20.0.4.tar.bz2.asc
~]# wget https://nextcloud.com/nextcloud.asc
~]# gpg -import nextcloud.asc
~]# gpg –verify nextcloud-20.0.4.tar.bz2.asc nextcloud-20.0.4.tar.bz2
</code>
</pre>
3. RPM 기반의 패키지들은 RPM-GPG-KEY라는 공개키 기반의 디지털 서명과 검증을 통해 해당 패키지의 버전과 그에 따른 
보증과 검증을 수행하여 때문에 Public GPG-KEY가 등록 되어있지 않은 상태에서는 yum을 사용할 수 없기 때문에 등록한다.

#### 3.6 압축 풀기
<pre>
<code>
~]# bunzip2 nextcloud-*.bz2
~]# tar -xvf nextcloud-20.0.4.tar
~]# cp -R nextcloud /var/www/html/
</code>
</pre>
* 콘텐츠를 웹 서버의 루트 디렉터리로 복사한다. 아파치 사용으로 /var/www/html 입니다.

<pre>
<code>
~]# mkdir /var/www/html/nextcloud/data
</code>
</pre>
* 설치 프로세스 중에는 데이터 폴더가 생성되지 않아 수동으로 디렉터리를 생성하였다.

<pre>
<code>
~]# Chown -R apache:apache /var/www/html/nextcloud
~]# systemctl restart httpd.service
</code>
</pre>
* nextcloud 전체 폴데에 Apache 사용자, 그룹 권한을 부여하고 데몬을 재시작한다.

<pre>
<code>
~]# firewall-cmd --zone=public --add-service=http --permanent
~]# firewall-cmd --reload
</code>
</pre>
* Apache 를 접근하도록 방화벽에 설정하고 활성화 시킨다.

#### 3.7 웹 접속 URL 확인
1. Nextcloud 설치가 끝났으면 /var/www/html/nextcloud/config/config.php 파일에서 웹 접근을 위한 경로를 확인한다.

~]# vim /var/www/html/nextcloud/config/config.php
<pre>
<code>
<?php
$CONFIG = array (
  'instanceid' => 'oc5qa6uhr5qj',
  'passwordsalt' => 'lSEQRm75mSF9MpG8y4zPBHrF+D+A1B',
  'secret' => 'Id0gGxWofZbINYLGouTjLeJJh36eOOsBY/lch1w532Sx5/m0',
  'trusted_domains' =>
  array (
    0 => '192.168.1.15',
  ),
  'datadirectory' => '/var/www/html/nextcloud/data',
  'dbtype' => 'sqlite3',
  'version' => '20.0.4.0',
  <span style="color:red">'overwrite.cli.url' => 'http://192.168.xx.xx/nextcloud'</span>, //URL 주소를 확인할 수 있다.
  'installed' => true,
  'memcache.distributed' => '\\OC\\Memcache\\Redis',
  'memcache.locking' => '\\OC\\Memcache\\Redis',
  'memcache.local' => '\\OC\\Memcache\\APCu',
  'redis' =>
  array (
    'host' => 'localhost',
    'port' => 6379,
  ),
  'maintenance' => false,
);
</code>
</pre>
* URL 을 통해 접근하면 관리자 웹 화면이 나타난다.

<img src="/assets/3.png" width="70%" height="400px" alt="NextCloud">
<img src="/assets/s1.JPG" width="70%" height="400px" alt="NextCloud">
* NextCloud 메인화면 입니다.

4.NextCloud 공통기능
----
#### 4.1 파일
<img src="/assets/s2.JPG" width="70%" height="400px" alt="NextCloud">
1. 사용자마다 개인 파일 관리와 다른 장치간 파일 공유를 하여 외부 저장소를 사용하여 파일 시스템 단위로 사용 및 관리한다.
2. NAS와 같은 기능으로 Up&Download 파일 이동이 가능합니다.
3. 네트워크 기반의 클라우드 서비스로 관리자 및 사용자 간 파일을 공유하거나 저장하여 사용 가능합니다.
4. SMB , SFTP , WebDav 기능을 통해 외부 저장소에서 파일을 관리 및 공유할 수 있습니다.
5. 활동 항목에서 파일에 대한 접근 및 작업을 하면 태스크 정보도 확인할 수 있습니다.

#### 4.2 사진
<img src="/assets/s3.JPG" width="70%" height="400px" alt="NextCloud">
1. 파일 항목에서 Photos 라는 디렉터리에 이미지를 업로드 하면 그림 기능에서 업로드 된 이미지 파일을 확인할 수 있습니다.
2. Cloud에서 많이 사용되는 사진 및 동영상 관리 시스템을 필수로 개인 이미지 또는 다른 사용자 간 공유하여 활용합니다.
3. 스프레드시트 , 프레젠테이션 제공하는 편집기를 통해 작업 가능하며 문서 작성을 위한 많은 Plugin기능을 제공합니다.

#### 4.3 활동
<img src="/assets/s4.JPG" width="70%" height="400px" alt="NextCloud">
1. 사용자마다 어느 항목에서 동작을 했거나, 파일을 수정 및 생성, 삭제 하였거나 캘린더 설정 및 채팅 이용시 태스크 정보를 기록해 줍니다.
2. 태스크 정보가 있으므로 누군가 임의로 변동 시 그 정보를 확인하기에 보안성이 있습니다.
3. 개인 및 다른 공유 형태로 통합적 사용으로 인해 추적할 수 있으며, 기본으로 제공하는 Plugin 입니다.

#### 4.4 토크
<img src="/assets/s5.JPG" width="70%" height="400px" alt="NextCloud">
1. NextCloud에서 제공하는 좋은 점은 파일 관리, 채팅, 캘린더 등 조직에서 사용하는 기능을 통합적으로 제공합니다.
2. 관리자에 권한에 의해서 사용자 간 채팅하여 MatterMost와 같은 기능을 제공합니다.
3. Nextcloud Talk는 Microsoft Teams 또는 Slack과 같은 다른 팀 공동 작업 플랫폼보다 커뮤니케이션을 더 잘 보호하여 데이터가 서버에 유지됩니다.
4. NextCloud Talk는 메타 데이터가 유출되는 것을 방지하여 다른 암호화 된 통신 기술보다 한층 더 나아갑니다.

#### 4.5 연락처
<img src="/assets/s6.JPG" width="70%" height="400px" alt="NextCloud">
1. 연락처 기능은 관리자와 사용자들의 연락처를 그룹화 하여 정보를 관리할 수 있다.
2. 전화번호, 이메일을 검색 기능을 통해 조회 가능하며, 개인 사용자마다 각각의 연락처를 관리할 수 있다.
3. 외부 저장소(External Storage)에서 등록한 다른 장치의 공유 파일에서도 연락처 정보를 가져올 수 있고, 개인 로컬에서도 가져올 수 있습니다.

#### 4.6 달력
<img src="/assets/s7.JPG" width="70%" height="400px" alt="NextCloud">
1. Google Calendar 기능과 유사하여 개인 캘린더, 다른 공유 캘린더를 사용 가능합니다.
2. 사용자 간 일정을 관리하고 공유하여 기업에서 업무 효율을 빠르게 처리할 수 있습니다.
3. 로컬 및 다른 장치간 공유 파일에서도 달력 정보에 대한 정보를 업로드 하여 가져올 수 있습니다.

5.외부 저장소(External Storage)
----
#### 5.1 외부 저장소
NextCloud 에서 제공하는 기능으로 외부 저장소(External Storage)에서 외부 저장소나 서비스 장치를 NextCloud 장치로 마운트할 수 있으며, 사용자가
개별 외부 저장소 서비스를 마운트할 수 있도록 허용 가능합니다.
<img src="/assets/ex.JPG" width="70%" height="400px" alt="NextCloud">

|저장소|내용|
|:-----------:|:---------|
|Amazon S3|웹 서비스 인터페이스를 사용하여 언제든지 웹 어디서나 원하는 양의 데이터를 저장하고 검색할 수 있는 인터넷 스토리지 서비스 입니다.|
|FTP|파일 전송 프로토콜(File Transfer Protocol) TCP/IP 프로토콜을 가지고 서버와 클라이언트 사이의 파일 전송을 하기 위한 프로토콜 입니다.|
|NextCloud|다른 NextCloud URL 주소와 사용자 계정을 통해 다른 사용자 간 공유적으로 사용할 수 있습니다.|
|SFTP|신뢰할 수 있는 데이터 스트림을 통해 파일을 접근, 파일을 전송, 파일을 관리하는 네트워크 프로토콜 입니다.|
|SMB/CIFS|윈도우에서 파일이나 디렉터리 및 주변 장치들을 공유하는데 사용되는 메시지 형식 입니다.|
|WebDav|하이퍼텍스트 전송 프로토콜(HTTP)의 확장으로, 월드 와이드 웹 서버에 저장된 문서와 파일을 편집하고 관리하도록 합니다.|
|로컬|내 PC나 물리적 서버에서 직접 사용하고 관리 중인 파일, 디렉터리를 경로를 설정하여 사용할 수 있도록 제공하는 기능입니다.|
|OpenStack|가상 리소스를 사용한다. Private 및 |

#### 5.2 인증
<img src="/assets/ex1.png" width="70%" height="400px" alt="NextCloud">

|인증|내용|
|:----------:|:-----------|
|1.	사용자 이름과 암호 |수동으로 정의 된 사용자 이름과 암호가 필요하며, 저장소로 직접 전달되며 마운트 지점 설정 중에 지정됩니다.|
|2.	로그인 인증 정보, 세션에 저장됨 |Nextcloud 로그인 자격 증명은 스토리지에 연결 하는 데 사용하는 체제로 서버의 어디에도 저장되지 않고 사용자 세션에 저장되어 보안을 강화합니다. 스토리지 자격 증명에 액세스 할 수 없고 백그라운드 파일 검색이 작동하지 않기 때문에 이 체제가 사용 중일 때 공유가 비활성화된다.|
|3.	로그인 자격 증명, 데이터베이스에 저장|사용자의 Nextcloud 로그인 자격 증명은 스토리지에 연결 하는데 사용하는 체제로 공유 비밀로 암호화 된 데이터베이스에 저장되며, 이 방법으로 마운트 지점 내에서 파일을 공유 할 수 있습니다.|
|4.	사용자는 데이터베이스에 저장|“사용자 이름과 암호”와 같은 방식으로 메커니즘의 작업을 하지만 자격 증명은 개별적으로 각 사용자에 의해 지정 될 필요가 있다. 해당 마운트에 처음 액세스하기 전에 사용자에게 자격 증명을 입력하라는 메시지가 표시된다.|
|5.	글로벌 자격 |마운트 포인트 대신 개인의 자격 증명을 위한 소스로 외부에 설정|

