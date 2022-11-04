# Gluesys Tech-blog

## 검토 개요

1. **목적**: 전달하는 정보의 타당성 검토 및 질적 향상
1. **적용 대상**: GitHub pull request로 올라간 기술 블로그 포스트
1. **방법**: GitHub pull request 코멘트 또는 사내 메신저를 통해 전달

## 주요 검토 사항

* 오탈자, 문법, 문맥 오류.
* 전달하는 내용이 검토자 본인이 알고 있는 상식이나 기술적 지식과 상이하지 않은지.
* 어떤 기술적 개념에 대한 설명이 충분하지 않아 부가적인 설명이 필요한지.
* 어떤 기술적 개념에 대한 예시가 적절한지.
* 최근 동향으로 설명되고 있는 부분이 본인이 알고 있는 것과 상이한지.
* 문장의 표현 및 서술 방식이 어색하거나 전문 분야의 문체와 크게 상이하지 않은지.
* 개념 및 동향에 대한 설명을 보조하기 위해 추가된 그림이나 표가 적절한지.
* 단락, 표, 그림의 제목이 내용과 상충하지 않거나 적절하지 않은지.
* 기타 보완 및 수정사항 전달. 

-----

# 글루시스 기술 블로그 포스트 작성 가이드라인

## 1. 개요
  
### 1.1 글루시스 기술 블로그 소개
  
 **목표**
  
 글루시스 기술 블로그는 글루시스 임직원의 기술 역량을 포스트에 담아내 외부에 어필하는 온라인 채널로, 다음과 같은 목표를 가지고 있습니다.   
  
 * 제공 콘텐츠에 대한 높은 전문성 및 객관성을 부각해 기업과 제품 기술에 대한 높은 신뢰 형성을 목표  
 * 관련 분야에 관심이 있는 관련 업계 종사자, 잠재고객, 구직자 대상으로 인지도 확보를 목표  
  
 **관리**
  
 글루시스 기술 블로그는 깃허브(GitHub)로 관리되며, 연구소 개발 3팀의 김지현 연구원이 담당자입니다.  
 - 글루시스 기술 블로그 깃허브 주소: https://github.com/gluesys/tech-blog
  
 **업로드 시기**
  
 블로그 포스트는 매월 연구소에서 1건, 기술부와 마케팅팀에서 1건으로 매월 2건씩 업로드하는 것이 목표이며, 매월 3\~4주 차(대략 19일\~25일 사이) 마케팅팀의 외부 뉴스레터 시기에 맞추어 업로드할 필요가 있습니다.  
  
&nbsp;
  
### 1.2 포스트 작성 시 인센티브
  
 글루시스에서는 기술 블로그 포스트 작성 시 다음과 같은 인센티브를 제공합니다.  
  
 **반기별 포상 제도**
  
 * 지급 시기: 기본 인센티브는 업로드 시 제공, 포상은 상반기와 하반기 워크샵 또는 월례회의 때 제공
 * 기본 인센티브: 작성 포스트 당 상품권 3만 원

| 포상 | 내용 | 금액 |
| -- | -- | -- |
| 인기 포스트상 | 신규 포스트 중 기간 내 방문 수 및 재방문 수가 가장 많은 포스트 대상 | 10만 원 |
| 우수 포스트상 | 신규 포스트 중 기간 내 평균 체류시간이 예상 수치와 근접, 이탈률 및 종료율이 가장 낮은 포스트 대상 | 10만 원 |
| 노력상 | 기간 내 포스트 작성 수가 가장 많은 사원 대상 (동률 발생 시 분할 지급) | 10만 원 |
  
 - 포스트 업로드 후 2달 후에 측정. 실질적으로 상반기는 전년도 12월\~5월, 하반기는 6월\~11월에 작성된 포스트만 측정 가능.
 - 원활한 통계 집계를 위해서는 월초 업로드를 지향.
 - 포스트 업로드는 매월 1번까지만 가능하며, 연속 업로드는 2번까지만 가능.
  
&nbsp;

## 2. 작성 전 준비사항
  
### 2.1 포스트 유형에서 주제 정하기
  
 기술 블로그 포스트를 작성하기로 업무에 할당되었다면, 우선 포스트의 주제를 결정해야 합니다.  
 글루시스 기술 블로그는 다음과 같이 6가지 유형의 포스트를 제공하며, 블로그의 목적에 맞게 해당 유형들을 기반으로 블로그 포스트의 주제를 선정할 필요가 있습니다.  
 아래 유형들을 제외한 다른 유형의 포스트를 작성하고 싶은 경우, 기술 블로그 담당자와 논의 후 결정할 필요가 있습니다.  
  
| 포스트 유형 | 주 내용 | 타겟 독자 |
| ---- | ---- | ---- |
| 기초 지식 | 기본이 되는 기술의 개념, 탄생 배경, 세부 분류, 연관 기술, 기술 비교, 적용 분야 등 최소한의 IT 배경지식이 요구되는 수준의 내용으로 구성. | 해당 기술 분야에 관심 있는 비전문가 |
| 심화 지식 | 기술의 적용 방법 및 절차, 특정 환경에서의 사용, 특정 경우의 대처, 실제 사례 소개 등 응용적인 요소 중심으로 구성. 기초지식 포스트와 연계해서 시리즈로 구성 가능. | 기술의 응용 방법에 관심 있는 비전문가 |
| 기술 동향 | 최신 기술 트렌드와 관련 키워드를 소개하고, 특정 산업 및 분야의 특성과 이에 요구되는 기술에 대한 소개를 위주로 구성. 기초지식 포스트와는 달리 최신 기술 위주로 주제 선정. | 최신 기술 트렌드에 관심 있는 업계 종사자 |
| 이벤트 후기 | 기술 세미나, 전시회, 강연 등의 이벤트 참가 후 업계 종사자 및 전문가 입장에서 최신 기술 트렌드, 타사 동향 등 경험한 내용의 서술과 그에 대한 견해 위주로 구성. | 최신 기술 트렌드에 관심 있는 업계 종사자 |
| 테스트 및 해결 | 특정 환경에서의 성능, 가용성 등을 증명하거나 특정 이슈 발생 시 해결 방법에 대한 내용들로 작성. 테스트나 해결책에 대한 방법론을 제시하고 그 과정을 단계별로 설명. | 해당 테마 관련 업무를 수행하는 전문가 |
| 제품 사용기 | 업계나 업무와 관련 있는 제품 및 툴에 대한 개요, 용도, 역사, 구조, 사례 등을 소개하고, 설치과정, 기능 등을 설명하는 방식으로 구성. 제품 리뷰 느낌으로 서술. | 해당 제품 및 툴을 사용하고자 하는 실무자 |
  
&nbsp;

### 2.2 작성 일정 공유하기
  
 기술 블로그 포스트의 주제가 선정되었다면, 포스트의 주제와 작성 진행 일정을 매터모스트나 이메일로 팀 내부와 마케팅팀에 전달해야 합니다.  
 마케팅팀에 일정을 공유하는 이유는 마케팅팀의 뉴스레터 배포 일정 전에 완성이 되어야 하기 때문입니다.  
  
 작성된 포스트가 최종적으로 블로그에 업로드되는데까지 다음과 같은 과정을 거치게 되니, 참고 후 일정을 조정하기 바랍니다.  
 1. 포스트 작성  
 2. 작성된 포스트를 깃허브에 풀 리퀘스트 올린 후 피드백 대기  
 3. 피드백 대응  
  
&nbsp;

## 3. 포스트 작성하기
  
### 3.1 작성 툴 준비하기
  
 블로그 포스트는 마크다운(.md) 파일로 업로드되며, 마크다운 파일을 수정할 수 있는 툴을 활용해 작성해야 합니다.  
 어떤 툴을 써야할지 모르는 분들에게는 `Notepad++`를 추천합니다. `Notepad++`는 해당 [링크](https://notepad-plus-plus.org/downloads/) 에서 다운로드 할 수 있습니다.  

&nbsp;

### 3.2 마크다운 문법 숙지하기
  
 글루시스 기술 블로그의 포스트는 마크다운 파일로 작성되며, HTML도 사용이 가능합니다.  
 마크다운 문법과 관련해서는 다음 링크를 참고하기 바랍니다: https://gist.github.com/ihoneymon/652be052a0727ad59601  

&nbsp;

### 3.3 기존 포스트를 참고해서 내용 작성하기
  
 글루시스 기술 블로그 깃허브에 [기존에 작성된 블로그 포스트](https://github.com/gluesys/tech-blog/tree/master/_posts/blog) 들을 템플릿 삼아 포스트를 작성할 수 있습니다.  
 포스트 파일은 기본적으로 다음과 같은 양식을 따라야 합니다:  
 * 파일명: `파일명`은 날짜와 포스트 주제 요약(영문)으로 구성됩니다(예: 2022-09-21-TrueNAS).  
 * 문서 정보: `문서 정보`는 포스트 내용의 최상단에 위치하며, `layout`, `title`, `date`, `categories`, `author`, `tags`, `cover`, `main`으로 구성됩니다.  
    - `layout`: 문서의 유형을 표시하는 부분이니 템플릿대로 놔두는 것을 권장합니다.  
    - `title`: 포스트의 제목을 적는 부분으로, 큰따옴표("") 안에 내용을 넣어야 합니다.  
    - `date`: 포스트 업로드 날짜를 적는 부분으로, `파일명`의 날짜와 동일하게 작성해야 합니다. 날짜 포맷은 `yyyy-mm-dd` 입니다.  
    - `categories`: 블로그 사이트의 상단 카테고리 부분으로, 현재로는 템플릿대로 놔두는 것을 권장합니다.  
    - `author`: 작성자를 말하며, 포맷은 `이름 (이메일 주소)` 입니다.  
    - `tags`: 포스트 내용과 관련된 태그를 말합니다. 태그는 한국어와 영어를 병행해 작성해야 하며, 포맷은 `[태그1, tag1, 태그2, tag2, ...]` 입니다. 영어 태그는 보통명사라도 첫 글자는 대문자로 써야 합니다.  
    - `cover`: 블로그 첫 페이지에 표시되는 포스트의 이미지를 말하며, 큰따옴표("") 안에 이미지의 위치를 넣어야 합니다(예: "/assets/SPDK_maincover.jpg"). 포스트에 쓰일 이미지 위치는 `assets` 폴더에 넣어야 하니 참고해 주시기 바랍니다.  
    - `main`: 블로그 포스트의 상단에 위치하는 이미지를 말하며, 큰따옴표("") 안에 이미지의 위치를 넣어야 합니다(예: "/assets/SPDK_maincover.jpg"). 포스트에 쓰일 이미지 위치는 `assets` 폴더에 넣어야 하니 참고해 주시기 바랍니다. 주로 `cover`와 같은 이미지를 쓰는 경우가 많습니다.  
 * 포스트 본문: 포스트의 주 내용을 말하며, `문서 정보` 아래에 위치합니다. 포스트 본문은 크게 제목, 내용, 첨부 이미지, 참고문헌, 각주 등으로 구성됩니다.  
    - 제목: 각 제목은 고유명사를 사용하는 것이 아닌 이상 한국어로 작성해 주시기 바랍니다. 최상위 제목은 `##`의 뎁스부터 시작하며, 특수문자 사용 시 [HTML 특수문자](http://kor.pe.kr/util/4/charmap2.htm) 를 써야 하니 참고해 주시기 바랍니다.  
    - 내용: 포스트의 내용은 구어체로 작성하되, 격식체를 유지해 주시기 바랍니다(예: ~입니다, ~습니다 등). 영어 약어나 내용에 핵심이 되는 고유명사에는 약어 또는 한국어 표기 단어 뒤에 괄호 안에 정식 영어 표기를 넣어야 합니다. 이후 영어 약어를 활용할 경우에는 괄호 안에 `이하 '영어 약어'`를 넣어야 합니다(예: 소프트웨어 정의 스토리지(Software Defined Storage, 이하 SDS)).  
    - 첨부 이미지: 내용 설명을 보조할 첨부 이미지는 중간 정렬 및 넓이를 700에서 800픽셀로 맞추고, 하단에 캡션을 넣어 주시기 바랍니다. 작성 방법은 템플릿을 참고해 주시기 바랍니다.  
    - 참고 자료: 해당 포스트를 작성하는데 참고한 자료의 링크나 레퍼런스를 불릿 형식으로 본문 바로 뒤에 기재해 주시기 바랍니다.  
    - 각주: 내용 중 보충 설명이 필요한 기술 개념이나 참조 링크를 참고 자료 뒤에 기재해 주시기 바랍니다. 각주 활용 방법은 템플릿을 참고해 주시기 바랍니다.  
 
&nbsp;

### 3.4 작성된 내용 스스로 검토하기
  
 포스트 작성을 마무리했다면 피드백을 요청하기 전에 최소 한 번이라도 다시 읽어보고 내용의 개연성이나 기술의 오류, 문법 오류, 오탈자가 있는지를 반드시 검토해 주시기 바랍니다.  
 이 과정이 생략된다면 나중에 피드백에 대응하는 과정이 길어지고 일정에 맞추지 못할 수도 있기 때문입니다.  
 문법 및 오탈자 확인은 다음 [링크](http://speller.cs.pusan.ac.kr/) 에서 빠르게 확인 가능하니 적극적으로 활용해 주시기 바랍니다.  

&nbsp;

## 4. 깃허브에 올리기

### 4.1 올리기 전 기본 세팅
  
 글루시스 기술 블로그는 기본적으로 깃허브에서 관리되고, 깃허브를 통해 피드백 대응을 하기 때문에 깃허브를 활용할 수 있어야 합니다.  
 깃허브를 활용하기 위해서는 우선 다음과 같은 요소들이 준비되어야 합니다:  
 * 깃(Git) 설치: 사용하는 PC에 깃 설치가 필요합니다. 깃 설치 및 기본적인 활용 방법은 [링크](https://backlog.com/git-tutorial/kr/) 를 참고 바랍니다.  
 * 깃허브 계정 만들기: 깃허브 계정이 없는 경우는 [링크](https://github.com/) 에서 계정 생성이 필요합니다.  
 * 글루시스 기술 블로그 저장소 포크하기: [글루시스 기술 블로그](https://github.com/gluesys/tech-blog) 깃허브 페이지의 우측 상단에 `Fork`를 클릭해 원격 저장소를 생성해 주시기 바랍니다.  
 * 로컬 저장소 만들기: 작성자 PC에 위 원격 저장소의 로컬 저장소를 생성해 주시기 바랍니다. 자세한 내용은 [링크](https://backlog.com/git-tutorial/kr/intro/intro2_2.html) 를 참고해 주시기 바랍니다.  
 * 최신 내용으로 동기화하기: 브랜치를 생성하기 전에 로컬 저장소를 최신으로 업데이트 해 주시기 바랍니다. 로컬 저장소가 현재 기술 블로그 저장소와 내용이 같거나 수정된 부분이 없어야 충돌 없이 머지가 가능하기 때문입니다.  
 * 브랜치 만들기: 로컬 저장소를 만들었으면 블로그 포스트만을 위한 브랜치를 만들어 주시면 좋습니다. 마스터 브랜치와 구분해 놓아야 관리가 편하기 때문입니다.  

&nbsp;

### 4.2 깃허브에 올려 검토 요청하기
  
 위의 기본 세팅이 완료되었다면, 다음과 같은 과정으로 깃허브에 올려 주시기 바랍니다:  
 1. 로컬 저장소의 내용 수정 및 업데이트: 작성한 마크다운 파일을 로컬 저장소의 `_post/blog` 경로에 올려 저장하고, `assets/<포스트명>/` 폴더에 커버 및 최상단 이미지, 첨부 이미지를 넣어 주시기 바랍니다.  
 2. 원격 저장소에 수정 내용 푸시: 파일을 커밋 후 원격 저장소에 푸시해 주시기 바랍니다. 커밋 메시지는 반드시 작성해야 하며 영문으로 커밋 내용을 작성할 필요가 있습니다. 자세한 내용은 [링크](https://backlog.com/git-tutorial/kr/intro/intro2_4.html) 를 참고해 주시기 바랍니다.  
 3. 기술 블로그 저장소에 풀리퀘스트 작성: 원격 저장소에 푸시가 성공했다면 원격 저장소 페이지에 나타난 `Create pull request` 버튼을 클릭해 풀리퀘스트를 작성할 수 있습니다. 포스트 제목과 요약 내용을 작성해서 풀리퀘스트를 올려 주시기 바랍니다.  
 4. 피드백 요청: 매터모스트의 `시스템` > `리뷰` 에 풀리퀘스트 페이지의 URL과 함께 리뷰를 요청해 주시기 바랍니다.  

&nbsp;

### 4.3 피드백 대응하기
  
 풀리퀘스트와 피드백 요청이 완료되었다면, 관계자들로부터 풀리퀘스트 페이지에 댓글로 피드백이 올라올 것입니다.  
 피드백 대응은 다음과 같은 과정으로 이루어집니다:  
 1. 피드백 코멘트의 내용 검토하기.  
 2. 피드백 내용을 로컬 저장소에서 수정 후 영문으로 작성된 커밋 내용과 함께 푸시하기.  
 3. 피드백 코멘트에 수정 내용을 댓글로 달고, 매터모스트 리뷰 채널에도 알리기.  
 4. 피드백을 준 사람은 수정 내용 확인 후 코멘트를 리졸브(resolve)하고, 전부 해결되면 어프루브(approve)하기.  
 5. 어프루브를 3번 이상 받으면, 최고 관리자에게 머지 요청하기.  
 6. 머지가 완료되어 업로드된 포스트를 블로그 페이지에서 최종적으로 확인하기.  

&nbsp;

이상으로 기술 블로그 포스트 작성과 관련하여 궁금하신 점이나 추가 의견이 있으신 분은 상기 기술 블로그 담당자나 가이드라인 작성자에 문의 바랍니다.
  