---
layout:     post
title:      "Nextcloud 파일 호스팅 서비스"
date:       2021-02-19 10:00:00
author:     이 태민 (tmlee@gluesys.com)
categories: blog
tags:      Cloud-오픈소스-클라우드-기능리뷰-스토리지-파일스토리지 
cover:      "/assets/IntelOptaneIMDT.png"
main:      "/assets/IntelOptaneIMDT_main.jpg"
---

====

1.Nextcloud 란?
----
Nextcloud는 파일 호스팅 서비스를 만들며 ownCloud 개발자인 Frank Karlitschek가 Fork하여 만들어진 클라우드 스토리지 소프트웨어 입니다.

직접 설치하여 운영할 수 있고 Office , Google Drive , MatterMost , Calendar 통합된 기능이면서 로컬 컴퓨터 또는 외부 파일 스토리지 호스팅에 사용할 수 있어 NAS 기술을 접하는 사람으로써 클라우드 스토리지 서비스에 적합합니다.

소프트웨어는 모듈식으로 추가 기능을 구현하기 위해 플러그인으로 확장할 수 있습니다.

Nextcloud 플랫폼은 개방형 프로토콜을 통해서 직접 설치할 수 있도록 다른 사용자에게 제공합니다.

<p align="center"><img src="/assets/1.JPG" width="1000px" height="400px">

위 표처럼 Nextcloud는 소프트웨어 플랫폼에서 통합된 기능들을 나열하고 보여 주고 있습니다.
파일 저장 및 공유 서비스를 포함하여 문서 작업, 가상화, 클라우드 컴퓨팅 기술 등 하나의 플랫폼에서 사용할 수 있어서 효율적이라고 생각이 됩니다. 

2.클라우드와 NAS(Network-Attached Storage) 
----

**클라우드의 기능**

 1. 파일을 따로 보관하고 동기화 할 수 있고 쉽게 공유할 수 있습니다.

 1. 로컬이나 외부로 문서를 액세스할 수 있습니다.

 1. 통합된 플러그인으로 사용자 간 전송할 수 있습니다.

 1. 삭제한 파일해도 기간 내 가져올 수 있으며, 파일 작업 시 자동으로 업데이트를 해줍니다.

**NAS 기능**

 1. NAS를 많은 사용자의 관점에서 단순히 백업용으로 생각하고 사용하고 있다. NAS는 파일 관리에 적합하여 기능에 대표적인 하나로 클라우드 서비스도 제공을 합니다.

 1. Petabyte나 Exabyte 같은 단위가 이제는 기업에서 폭발적으로 사용하는 데이터 활용에 있어서 대응 및 서비스를 하기 위해 활용성이 떨어지는 데이터와 활용성이 높은 데이터를 분류할 수도 있습니다.

 1. NAS는 '네트워크 드라이브'나 '외부 저장장치의' 형태로만 사용되고 Cloud 서비스를 이용하면 '동기화 방식'이 기본으로 되어 용량이 늘어나면서 NAS와 같이 활용되는 목적으로 구축된다고 합니다.

 1. NAS는 하드디스크에 의존하고, Raid구성으로 비용도 많이 드는데, 클라우드 서비스는 휴지통이나 , 파일 히스토리 기능을 지원하여 복구가 수월하다고 생각되어 안정성이 보장된다고 생각이 됩니다.

<p align="center"><img src="/assets/2.JPG" width="1000px" height="400px">

3.Nextcloud 설치
----
* CentOS 7.9 , PHP7.2 , MariaDB 배포하고 Apache에서 실행되는 Nextcloud를 배포합니다.
* CentOS 7을 설치하여 성공적인 플랫폼을 제공하도록 구축 하였습니다.
<pre>
<code>
   # 최신 커널 업데이트를 진행합니다.
~]# yum update -y 
   # Apache 웹 서버 패키지를 설치합니다.
~]# yum install -y httpd 
</code>
</pre>

#### 3.1 Apache 설정 -> vim /etc/httpd/conf.d/nextcloud.conf
<pre>
<code>
<VirtualHost *:80>
   # 실제 소스파일이 있는 Web Root 지정소
  DocumentRoot /var/www/html  
   # 서비스 할 도메인 지정소
  ServerName test.domain.com  
<Directory "/var/www/html/">
   # 디렉터리에 대한 액세서 허용
  Require all granted  
   # 접근자를 모두 허락하도록 설정
  AllowOverride All    
   # 디렉터리에 대한 특정 옵션 설정
  Options FollowSymLinks MultiViews  
</Directory>
</VirtualHost>
</code>
</pre>

<pre>
<code>
   # Apache Web Service 데몬을 enable 시키고 start 시킵니다.
~]# systemctl enable httpd.service
~]# systemctl start httpd.service
</code</pre>
</pre>

#### 3.2 PHP 관련 패키지 설치
* Nextcloud는 PHP 프로그래밍 언어를 사용하여 새로운 모듈을 만들고 싶으면 (현재 최신) 7.3이상의 패키지를 설치합니다.
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
* httpd 설치 경로 /opt/rh/httpd24에서 Nextcloud 설정 경로와 심볼릭 링크를 설정하였습니다.

#### 3.4 MariaDB 설치
<pre>
<code>
~]# yum install -y mariadb mariadb-server
~]# systemctl enable mariadb.service
~]# systemctl start mariadb.service
</code>
</pre>
* 이 작업을 완료 한 후 Nextcloud가 액세스 할 수 있도록 사용자 이름과 비밀번호로 데이터베이스를 생성합니다.

#### 3.5 Nextcloud 설치
1. [Nextcloud Install](https://nextcloud.com/install/)
* Nextcloud Server 다운로드 -> 다운로드 -> 서버 소유자 용 아카이브 파일로 이동하여 tar.bz2 다운로드 하였습니다. 
2. GPG KEY 오류로 인한 yum install 실패시 해결하기 위한 조치사항입니다.
<pre>
<code>
~]# wget https://download.nextcloud.com/server/release/nextcloud-20.0.4.tar.bz2.asc
~]# wget https://nextcloud.com/nextcloud.asc
~]# gpg -import nextcloud.asc
~]# gpg –verify nextcloud-20.0.4.tar.bz2.asc nextcloud-20.0.4.tar.bz2
</code>
</pre>
3. RPM 기반의 패키지들은 GPG KEY 라는 공개키 기반의 디지털 서명과 검증을 통해서 각종 소스의 변조 유뮤를 검사해주고 무결성을 제공하여 허가된 사용자만 권한을 가질 수 있습니다. 

#### 3.6 압축 풀기
<pre>
<code>
~]# bunzip2 nextcloud-*.bz2
~]# tar -xvf nextcloud-20.0.4.tar
~]# cp -R nextcloud /var/www/html/
</code>
</pre>
* 콘텐츠를 웹 서버의 루트 디렉터리로 복사한다. Apache 사용으로 **/var/www/html** 입니다.

<pre>
<code>
~]# mkdir /var/www/html/nextcloud/data
</code>
</pre>
* 설치 프로세스 중에는 데이터 폴더가 생성되지 않아 수동으로 디렉터리를 생성하였습니다.

<pre>
<code>
~]# Chown -R apache:apache /var/www/html/nextcloud
~]# systemctl restart httpd.service
</code>
</pre>
* Nextcloud 전체 폴더에 Apache 사용자, 그룹 권한을 부여하고 데몬을 재시작합니다.

<pre>
<code>
~]# firewall-cmd --zone=public --add-service=http --permanent
~]# firewall-cmd --reload
</code>
</pre>
* Apache를 접근하도록 방화벽에 설정하고 활성화를 시킵니다.

#### 3.7 웹 접속 URL 확인
1. Nextcloud 설치가 끝났으면 **/var/www/html/nextcloud/config/config.php** 파일에서 웹 접근을 위한 경로를 확인합니다.

<pre>
<code>
~]# vim /var/www/html/nextcloud/config/config.php
</code>
</pre>

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
* URL 을 통해 접근하면 관리자 웹 화면이 나타나는 걸 확인할 수 있습니다.

<p align="center"><img src="/assets/3.png" width="700px" height="400px">
<p align="center"><img src="/assets/s1.JPG" width="700px" height="400px">

* Nextcloud 메인화면 입니다.

#### 3.8 에이전트 접속 확인

**[Desktop , Mobile Nextcloud Install](https://nextcloud.com/install/)**

<p align="center"><img src="/assets/agent3.JPG" width="700px" height="400px">

1. Nextcloud Install 링크를 들어가면 Desktop과 Mobile 전용 탐색기 2개 에이전트가 있습니다.
 
<p align="center"><img src="/assets/agent4.JPG" width="700px" height="400px">

2. Desktop 클라이언트를 설치합니다.

<p align="center"><img src="/assets/agent5.JPG" width="700px" height="400px">

3. Mobile 클라이언트를 설치합니다.
 
<p align="center"><img src="/assets/agent.JPG" width="700px" height="400px">

4. Nextcloud Install 사이트에서 전용 탐색기 설치를 받으면 압축을 풉니다.
5. 탐색기 접근 전에 계정 접근을 위한 웹(https://)에서 로그인하여 에이전트 접근을 허용합니다.
6. 이메일을 통한 계정 접근과 URL을 통한 계정 접근 2가지 방법이 에이전트에서 가능합니다.

<p align="center"><img src="/assets/agent1.jpg" width="700px" height="400px">

7. 계정 접근이 활성화 되면 윈도우에서 Nextcloud 앱이 실행됨을 확인할 수 있습니다.
8. 웹과 유사하게 모든 기능을 사용할 수 있고 활동 기록도 확인할 수 있습니다.

<p align="center"><img src="/assets/agent2.JPG" width="700px" height="400px">

9. 내 PC에서 Nextcloud가 자동으로 네트워크 드라이브 연결이 되며, 에이전트를 통해서 파일을 관리 및 사용할 수 있습니다.


4.NextCloud 기능
----
#### 4.1 파일
<p align="center"><img src="/assets/s2.JPG" width="700px" height="400px">

1. 사용자마다 개인 파일을 관리하고 서로 다른 장치 간 파일 공유를 하여 파일을 관리 및 사용합니다.
2. 네트워크 기반의 클라우드 서비스로 관리자 및 사용자 간 파일을 공유하거나 저장하여 사용 가능합니다.
3. SMB , SFTP , WebDAV 프로토콜을 통해 외부 저장소에서 파일을 관리 및 공유할 수 있습니다.
4. 해당 파일에 대한 사용자 간 댓글 기능을 사용할 수 있습니다.

#### 4.2 사진
<p align="center"><img src="/assets/s3.JPG" width="700px" height="400px">

1. 파일 항목에서 Photos 라는 디렉터리에 이미지를 업로드 하면 그림 기능에서 업로드 된 이미지 파일을 확인할 수 있습니다.
2. 클라우드에 많이 사용되는 사진 및 동영상 관리 시스템을 필수로 개인 이미지 또는 다른 사용자 간 공유하여 활용합니다.
3. 스프레드시트 , 프레젠테이션 제공하는 편집기를 통해 작업 가능하며 문서 작성을 위한 많은 플러그인 기능을 제공합니다.

#### 4.3 활동
<p align="center"><img src="/assets/s4.JPG" width="700px" height="400px">

1. 사용자마다 어느 항목에서 동작을 했거나, 파일을 수정 및 생성, 삭제 하였거나 캘린더 설정 및 채팅 이용시 활동 기록을 해줍니다.
2. 활동 기록으로 다른 사용자가 임의로 변동 시 그 정보를 확인할 수 있습니다.
3. 개인 및 다른 공유 형태로 통합적 사용으로 인해 추적할 수 있으며, 기본으로 제공하는 플러그인 입니다.

#### 4.4 토크
<p align="center"><img src="/assets/s5.JPG" width="700px" height="400px">

1. Nextcloud에서 제공하는 좋은 점은 파일 관리, 채팅, 캘린더 등 조직에서 사용하는 기능을 통합적으로 제공합니다.
2. 관리자에 권한에 의해서 사용자 간 채팅하여 Mattermost와 같은 기능을 제공합니다.
3. Nextcloud Talk는 Microsoft Teams 또는 Slack과 같은 다른 팀 공동 작업 플랫폼보다 커뮤니케이션을 더 잘 보호하여 데이터가 서버에 유지됩니다.

#### 4.5 연락처
<p align="center"><img src="/assets/s6.JPG" width="700px" height="400px">

1. 연락처 기능은 관리자와 사용자들의 연락처를 그룹화 하여 정보를 관리할 수 있습니다.
2. 전화번호, 이메일 검색 기능을 통해 조회 가능하며, 개인 사용자마다 개인 연락처를 관리할 수 있습니다.
3. 외부 저장소(External Storage)에서 등록한 다른 장치의 공유 파일에서도 연락처 정보를 가져올 수 있고, 개인 로컬에서도 가져올 수 있습니다.

#### 4.6 달력
<p align="center"><img src="/assets/s7.JPG" width="700px" height="400px">

1. 구글 캘린더 기능과 유사하여 개인 캘린더, 다른 공유 캘린더를 사용 가능합니다.
2. 사용자 간 일정을 관리하고 공유하여 기업에서 업무 효율을 빠르게 처리할 수 있습니다.
3. 로컬 및 다른 장치간 공유 파일에서도 달력 정보에 대한 정보를 업로드 하여 가져올 수 있습니다.

5.외부 저장소(External Storage)
----
#### 5.1 외부 저장소
Nextcloud 에서 제공하는 기능으로 외부 저장소에서 외부 저장소나 서비스 장치를 Nextcloud 장치로 마운트할 수 있으며, 사용자가 개별 외부 저장소 서비스를 마운트할 수 있도록 허용 가능합니다.
![Alt textxr](/assets/ex.JPG)

|저장소|내용|
|:-----------:|:---------|
|Amazon S3|웹 서비스 인터페이스를 사용하여 언제든지 웹 어디서나 원하는 양의 데이터를 저장하고 검색할 수 있는 인터넷 스토리지 서비스 입니다.|
|FTP|서버와 클라이언트 사이의 파일 전송을 하기위한 프로토콜입니다.|
|Nextcloud|다른 Nextcloud URL 주소와 사용자 계정을 통해 다른 사용자 간 공유적으로 사용할 수 있습니다.|
|SFTP|신뢰할 수 있는 데이터 스트림을 통해 파일을 접근, 파일을 전송, 파일을 관리하는 네트워크 프로토콜 입니다.|
|SMB/CIFS|윈도우에서 파일이나 디렉터리 및 주변 장치들을 공유하는데 사용되는 메시지 형식 입니다.|
|WebDAV|하이퍼텍스트 전송 프로토콜(HTTP)의 확장으로 , 월드 와이드 웹 서버에 저장된 문서와 파일을 편집하고 관리하도록 합니다.|
|로컬|내 PC나 물리적 서버에서 직접 사용하고 관리 중인 파일, 디렉터리를 경로를 설정하여 사용할 수 있습니다.|
|OpenStack 객체 저장소|객체 저장소 내 폴더의 매핑을 관리하고 외부 저장소에 파일을 저장 및 관리합니다.|

#### 5.2 인증
<p align="center"><img src="/assets/ex1.png" width="700px" height="400px">

|인증|내용|
|:----------:|:-----------|
|사용자 이름과 암호 |수동으로 정의 된 사용자 이름과 암호가 필요하며, 저장소에 계정 및 패스워드를 설정하여 마운트를 합니다.|
|로그인 인증 정보, 세션에 저장됨 |Nextcloud 로그인 자격 증명은 스토리지에 연결 하는 데 사용하는 체제로 서버의 어디에도 저장되지 않고 사용자 세션에 저장되어 보안을 강화합니다. 스토리지 자격 증명에 액세스 할 수 없고 백그라운드 파일 검색이 작동하지 않기 때문에 이 체제가 사용 중일 때 공유가 비활성화된다.|
|로그인 자격 증명, 데이터베이스에 저장|사용자의 Nextcloud 로그인 자격 증명은 스토리지에 연결 하는데 사용하는 체제로 공유 비밀로 암호화 된 데이터베이스에 저장되며, 이 방법으로 마운트 지점 내에서 파일을 공유 할 수 있습니다.|
|사용자는 데이터베이스에 저장|“사용자 이름과 암호”와 같은 방식으로 메커니즘의 작업을 하지만 자격 증명은 개별적으로 각 사용자에 의해 지정 될 필요가 있다. 해당 마운트에 처음 액세스하기 전에 사용자에게 자격 증명을 입력하라는 메시지가 표시됩니다.|
|글로벌 자격 |마운트 포인트 대신 개인의 자격 증명을 위한 소스로 외부에 설정 합니다.|

작성 후기
----

* * *
클라우드 서비스를 제공하는 오픈소스 기반의 Nextcloud 를 소개하였습니다. NAS 엔지니어로서 파일 시스템 기반의 스토리지와 파일 호스팅 서비스인 Nextcloud가 통합된 서버에서 구축하여 진행하였습니다. 통합된 정보를 저장하고 운영할 수 있는 공용 데이터들을 쉽고 안정성있게 관리할 수 있다고 깨달았습니다. 오픈소스 기반의 인프라 및 플랫폼 기술을 더 많이 접하고 공유할 수 있도록 할 것입니다.
* * *
