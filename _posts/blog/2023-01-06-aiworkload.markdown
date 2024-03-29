---
layout:     post
title:      "AI 워크로드에 적합한 스토리지"
date:       2023-01-06
author:     박주형 (jhpark@gluesys.com)
categories: blog
tags:       [인공지능, Artificial Intelligence, AI, 머신러닝, Machine Learning, 딥러닝, Deep Learning, ]
cover:      "/assets/aiworkload_maincover.jpg"
main:       "/assets/aiworkload_maincover.jpg"
---

블로그 포스트 작성을 시작하려고 텅 빈 문서 화면을 볼 때마다 누군가가 대신 작성해 주었으면 좋겠다는 생각을 가끔 하게 됩니다. 그러다 우연히 블로그 포스트를 자동으로 작성해 주는 Copy.ai라는 웹 애플리케이션을 발견하게 되었습니다. Copy.ai는 GPT-3[^1]를 기반으로 한 AI 기반 웹서비스로, 핵심 토픽과 키워드, 문단 별 주제를 입력하면 순식간에 글을 작성해 주는데 생각보다 글의 흐름이나 문장의 완성도가 매우 높았습니다.  
  
이와 같은 기술을 구현하기 위해서는 고성능 서버뿐만 아니라, 데이터가 저장되는 스토리지 선택에도 많은 고민이 필요합니다. AI 워크로드는 기본적으로 매우 대용량이며 동시에 고성능이 요구된다는 점에서 일반적인 워크로드와 상이하며, 그에 맞는 스토리지 인프라 계획을 수립하기 위해서는 먼저 AI 워크로드에 대해 정확히 이해할 필요가 있습니다.  
  
이번 포스트에서는 AI 워크로드에 필요한 스토리지의 기본적인 특성에 대해 알아보고, AI 워크로드의 유형과 그에 따른 스토리지의 요구사항, 그리고 각각의 스토리지 타입에 따른 장단점을 비교해 보고자 합니다.  

&nbsp;

## AI 워크로드의 종류
  
기본적으로 스토리지에 대한 요구 사항은 데이터의 크기나 입출력 패턴 등에 따라 달라집니다. 데이터에 접근하는 빈도나 처리량, 데이터의 크기(종류에 따라 작게는 1KB 이하부터 크게는 수 GB까지)에 따라 요구되는 스루풋이나 IOPS, 확장성 등이 다르기 때문인데요, AI 워크로드의 유형에 따라 데이터셋의 규모나 증가하는 데이터의 양 역시 다를 수 있기 때문에, 도입하는 스토리지 종류나 데이터 예상 성장 규모를 정하기 위해서는 이러한 특성을 아는 것이 매우 중요합니다.  
  
AI 워크로드의 유형은 다음과 같습니다:  
  
 * **머신러닝 및 딥러닝:** 머신러닝 및 딥러닝(이하 ML/DL) 워크로드는 저장된 데이터셋을 활용해 의사결정 트리나 인공 신경망 모델을 훈련시켜 스토리지에 높은 입출력 성능이 요구되는 작업입니다. 활용하는 데이터의 양에 따라서 모델의 정확도가 높아지기 때문에 기본적으로 저장되는 데이터의 규모가 매우 크고, 데이터를 수집하고 정제하면서 생성되는 데이터로 인해 항상 스토리지 공간의 확장을 감안해야 합니다. 딥러닝 애플리케이션의 경우에는 머신러닝에 비해 데이터를 불러오고 처리하는 빈도가 높다는 특성도 있습니다.  
  
 * **자연어 처리:** 자연어 처리(Natural Language Processing, 이하 NLP)는 컴퓨터가 언어의 의미나 문장의 구조 등을 인식하고 이해하도록 학습시키는 작업입니다. 앞에서 언급한 OpenAI의 GPT-3가 NLP의 가장 대표적인 모델 중 하나입니다. NLP 역시 고집적 입출력 성능과 낮은 지연시간을 요구하기는 하지만, 사용되는 데이터셋이 텍스트 중심이다 보니 다른 워크로드 유형에 비해 많은 스토리지 공간을 요구하지는 않습니다. 단적인 예로 GPT-3는 고작 800GB 정도만 필요로 합니다.  
  
 * **추천 시스템:** 추천 시스템은 웹사이트 등에서 사용자의 행동 패턴을 분석해 사용자의 취미나 관심사에 맞는 정보를 분석하고 제공하는 기술로, 지금까지의 모든 사용자의 행동 기록들을 데이터셋으로 삼아 학습시키는 작업을 수행합니다. 추천 시스템은 실시간 정보를 분석해 결과를 사용자에게 바로 전달해야 하므로, 스토리지에서 대규모 데이터셋을 최대한 빨리 불러올 수 있어야 합니다. 또한, 트렌드에 민감한 시스템의 특성상 패턴의 변화를 빠르게 인식할 수 있어야 하므로, 데이터의 사용 기한을 정해 티어를 구분하는 것과 오래된 데이터의 백업 및 아카이빙에 대해서도 고민해야 합니다.  
  
 * **컴퓨터 비전:** 컴퓨터 비전은 AI 모델을 활용해 컴퓨터가 영상이나 이미지 등에서 얻은 정보를 분석해 특정 행동이나 방안을 제안하는 기술로, 자율 주행이나 이미지 분석 등에 주로 활용됩니다. 주로 영상이나 이미지 등 대용량 데이터를 활용하기 때문에 데이터셋의 규모가 남다르고, 영상의 프레임을 이미지로 변환하거나 고해상도 이미지를 작게 쪼개는 작업을 수행하기 때문에 고 확장 및 대용량에 대한 요구뿐만 아니라, 높은 스루풋과 IOPS를 가지는 스토리지 인프라를 필요로 합니다.  
  
&nbsp;

## AI 워크로드 처리 과정 별 스토리지 요구사항
  
AI 워크로드의 종류 중에서도 AI의 학습 단계에 따라 스토리지의 요구사항이 달라집니다. 머신러닝과 딥러닝을 위시한 AI 학습은 인간의 사고를 모방해 데이터에서 추출한 정보의 패턴을 학습하는 프로세스를 기계로 구현하는 작업입니다. AI 학습은 기본적으로 데이터 수집, 데이터 가공, AI 모델 훈련, 데이터 준비 및 아카이빙의 단계로 나뉘어지며, 단계별 스토리지의 역할과 요구사항은 다음과 같습니다:  
  
 * **데이터 수집:** 학습에 필요한 데이터를 수집하는 단계입니다. 인프라 내 산재되어 있는 데이터를 수집하려면 다양한 프로토콜과 애플리케이션을 지원할 수 있어야 하며, 다양한 데이터를 수집해 스토리지에 저장하는 데에는 주로 순차 쓰기가 발생합니다. 데이터 집약적인 특성상 대규모 저장공간을 필요로 합니다.  
  
 * **데이터 가공:** 훈련에 필요한 데이터를 전처리하는 단계입니다. 수집한 데이터를 분류하고 정제하는 등의 전처리 작업을 위해서는 높은 IOPS를 지원할 수 있어야 하고, 여기서는 랜덤 및 순차 읽기/쓰기가 같이 발생합니다.  
  
 * **AI 모델 훈련:** AI 모델을 활용해 데이터의 패턴에 대한 훈련을 수행하는 단계입니다. 이 단계는 AI 워크플로우 중에서도 가장 고성능이 요구되는 단계입니다. 모델 훈련을 위해 데이터셋을 읽어오는 시간에 따라 수 시간에서 며칠이 걸릴 수 있는 단계이기 때문에 매우 낮은 지연시간과 높은 스루풋을 필요로 합니다. 훈련이 끝나면 훈련 성과를 시범 데이터로 평가해 결과가 수준 미달이면 데이터 가공 및 모델 훈련 단계로 다시 넘어갑니다.  
  
 * **데이터 준비 및 아카이빙:** AI 모델을 배포하고 모델의 성능을 평가 및 테스트하는 단계입니다. 배포된 AI 모델을 모니터링하고 성능을 지속적으로 평가하기 위해 대규모의 액티브 아카이브용 스토리지가 필요합니다.  

&nbsp;

## AI 워크로드에 적합한 스토리지의 특성
  
AI 워크로드는 대규모 데이터를 활용해 AI 모델을 훈련시키고, 완성된 AI 모델을 지속적으로 활용하는 작업을 수행합니다. 이를 감당하기 위해서는 기본적으로 높은 성능과 대규모 저장 용량을 가진 스토리지가 필요합니다. AI 워크로드에는 다음과 같은 스토리지 특성이 요구됩니다:  
  
&nbsp;

### 고성능 및 저지연성
  
AI 솔루션의 컴퓨팅을 담당하는 서버에 비싼 GPU를 탑재해 고성능 컴퓨팅을 제공한다고 하더라도 스토리지의 성능이 부족하면 병목이 발생할 수 있습니다. 이 때문에 AI 서비스를 위한 스토리지는 대용량의 데이터셋을 시간당 수 TB의 스루풋으로 고성능 서버에 제공할 수 있어야 하며, 입출력에 따른 지연시간을 최소화해 훈련 시간을 단축시킬 수 있어야 합니다.  

&nbsp;

### 병렬 입출력 구성
  
병렬 스토리지 아키텍처는 고성능 GPU 서버의 AI 워크로드를 감당할 수 있는 방법 중 하나입니다. 여러 대의 스토리지 노드로 글로벌 파일시스템 환경을 구성해 데이터를 여러 스토리지 노드에 분산 저장하고, 동시에 각 노드로부터 병렬로 빠르게 처리할 수 있습니다. 이에 따라 스토리지에 걸리는 성능 부하를 분산시키고, 응답시간도 그만큼 줄일 수 있습니다. AI 모델 훈련과 같이 매우 높은 스루풋과 낮은 응답시간이 요구되는 워크로드에서도 스토리지 병목을 최소화할 수 있습니다.  

&nbsp;

### 높은 확장성
  
AI 모델 훈련에는 기본적으로 많은 양의 데이터가 사용될수록 정확도가 높아집니다. 이 데이터들은 여러 소스에서 다양한 포맷으로 수집되며, AI 모델의 정확도를 선형적으로 증가시키기 위해서는 보다 많은 데이터가 지속적으로 투입되어야 합니다. 이에 따라 데이터가 저장되는 스토리지 역시 데이터의 증가 추세에 따라 최적의 비용으로 증설하는 것을 기본 전략으로 세워야 합니다.  

&nbsp;

## 스토리지 타입 비교
  
지금까지 AI 워크로드에 적합한 스토리지의 요구사항과 특성에 대해 각각 다른 관점에서 알아보았는데요, 그렇다면 이번에는 어떤 스토리지 타입이 AI 워크로드에 적합한지에 대해 알아보고자 합니다.  
  
 * **블록 기반 스토리지:** 블록 기반 스토리지는 가장 빠른 스루풋과 낮은 지연시간을 제공하기 때문에 전통적으로 고성능 스토리지가 필요한 환경에 주로 도입되어 왔습니다. 하지만, 고성능 컴퓨팅에 필요한 대규모 비정형 데이터의 증가 추세를 감당하기에는 확장성이 떨어진다는 단점이 있습니다.  
  
 * **파일 기반 스토리지:** 파일 기반 스토리지는 계층적 파일 구조로 비정형 데이터를 저장하는 데 적합하고, 스케일아웃 파일 시스템을 활용해 높은 확장성을 제공합니다. 게다가 NFS나 SMB/CIFS와 같이 범용성이 뛰어난 파일 공유 프로토콜을 사용하기 때문에 접근성도 뛰어납니다. 다만, 블록 스토리지에 비해 성능이 상대적으로 떨어지는 단점이 있습니다.  
  
 * **오브젝트 스토리지:** 오브젝트 스토리지는 메타데이터가 오브젝트와 함께 저장되기 때문에 대규모 데이터를 저장하는 환경에서는 최고의 확장성을 제공하고, HTTP를 통한 단순한 접근성도 제공합니다. 게다가 많은 AI/ML 애플리케이션이 퍼블릭 클라우드 인터페이스를 지원한다는 장점도 있습니다. 하지만 파일 기반 스토리지와 마찬가지로 블록 스토리지에 비해 상대적으로 성능이 떨어지는 편이고, 성능과 사용량에 따라 퍼블릭 클라우드의 유지 비용이 매우 높다는 부분도 고려할 점입니다.  
  
이렇게 스토리지의 타입에 따른 장단점을 정리해 보았습니다만, 실제로는 블록과 파일 및 오브젝트 스토리지를 같이 쓰는 하이브리드 구성을 채용하는 경우도 있습니다. 고성능 블록 스토리지나 스케일아웃 파일 스토리지에 활용도가 높은 데이터를 저장하고, 오브젝트 스토리지를 액티브 아카이브로 활용해 활용도가 낮은 데이터를 저장하는 구성으로 비용 최적화를 구현하기도 합니다. 또한, 무작정 올 플래시 스토리지 위주로 도입하는 것보다는, 하드디스크를 콜드 티어로 활용해 하이브리드 환경을 구성하거나, 멀티 클라우드 전략을 통해 대용량 데이터 증가에 대한 비용 부담을 최소화하는 방법도 있습니다. 다만, 스토리지 간 데이터 이동에 지연시간이 발생하는 경우 그만큼 AI 모델 학습에도 성능 저하를 일으킬 수도 있다는 점도 감안해야 합니다.  

&nbsp;

## 마치며
  
AI 워크로드는 기존의 다른 워크로드에 비해 기술 집약적이면서 구현 비용이 높은 것이 특징입니다. 최근 들어서는 스토리지 단에서도 GPU나 가속기를 활용해 스토리지의 성능을 향상시키거나, 컴퓨팅 서버의 연산처리의 일부를 분담하는 기술들이 등장하고 있어 신기술에 대한 지속적인 이해도 필요합니다. 이 때문에 제대로 도입하기 위해서는 시간과 노력을 들여서 AI 워크로드의 모든 단계에 걸쳐서 스토리지 요구사항을 조사하고, 자사 인프라에 맞는 스토리지 구성과 향후 증설 계획을 수립할 수 있어야 합니다.  



&nbsp;

--- 

### 참고

 * https://www.techtarget.com/searchstorage/feature/Storage-strategies-for-machine-learning-and-AI-workloads
 * https://www.techtarget.com/searchstorage/tip/8-factors-that-make-AI-storage-more-efficient
 * https://www.computerweekly.com/feature/Storage-requirements-for-AI-ML-and-analytics-in-2022?_gl=1*1rx8hff*_ga*ODQyMTg0NzMuMTY2NzUyOTMyNA..*_ga_TQKE4GS5P9*MTY3MjAzMTI3NS4zOS4xLjE2NzIwMzQyNDguMC4wLjA.&_ga=2.223461979.1707321966.1672013822-84218473.1667529324
 * https://lambdalabs.com/blog/demystifying-gpt-3
 * https://www.hitachivantara.com/en-us/insights/top-5-workloads-changing-how-we-think-about-storag.html
 * https://en.wikipedia.org/wiki/GPT-3
 * https://www.weka.io/blog/storage-for-ai-ml-workloads/



### 주석

[^1]: **GPT-3**는 OpenAI에서 개발한 딥러닝 기반의 대형 언어 모델입니다. GPT-3는 현존하는 AI 모델 중에서 자연어를 해석하는데 있어서 가장 높은 정확도를 가지는 자연어 처리 AI 모델로, 약 1,750억개의 매개변수와 4,990억 개의 토큰을 사용해 학습했다고 합니다.  
  