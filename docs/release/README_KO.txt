닌자군 - 마성의 모험 (NES/패미컴) 한글 패치 v1.0

번역 범위: 타이틀 로고 忍者くん → 닌자군.
인원 메뉴·HUD·시작 안내·게임 오버·보너스 등 기존 영문은 유지합니다.
사용자 플레이에서 타이틀 외 일본어를 발견하지 못했다는 보고를 받았습니다.
에이전트 조사에서도 추가 일문은 확인되지 않았으나 전 씬 완주 판정은 아닙니다.

Windows 적용 방법
1. ZIP 전체를 압축 해제합니다.
2. 지원 일본판 원본 NES 파일을 apply.cmd 위로 끌어 놓습니다.
3. 같은 폴더에 Ninja_kun_Majou_no_Bouken_KR_v1.0.nes가 생성됩니다.
원본과 기존 결과 파일은 덮어쓰지 않습니다.
별도 출력 경로: apply.cmd "원본 경로.nes" "새 결과 경로.nes"
Windows PowerShell 5.1과 .NET을 사용하며 별도 실행 파일은 포함하지 않습니다.
다른 운영체제에서는 BPS 지원 패처로 BPS를 원본에 적용하고 아래 결과 해시를 확인하세요.
이전 개발용 IPS는 이 배포물에 포함하지 않습니다.

지원 원본: Ninja-kun - Majou no Bouken (Japan), iNES 헤더 포함 24,592바이트.
원본 SHA-256: 7d4e1f61f8f7464d73a35c5118f59227dd7d7ddd6c3c2a62e42f5a0ac9477978
결과 SHA-256: 325109b789525c781cb72e78392768df8625fd55c04f78f329ece540993cf51d
BPS SHA-256: de06bb9d99b37a76ea7dc92a71fed1fc324bbc1668ba7aa5748734c3d839d2a0

그래픽 공간 확보를 위해 출력 ROM은 매퍼3(CNROM), PRG32KiB/CHR16KiB, 49,168바이트입니다.
원래 NROM 카트리지 회로와 다릅니다. CNROM 지원 에뮬레이터에서 새로 부팅하세요.
원본 ROM용 세이브스테이트를 그대로 불러오지 마세요.
Mesen2.1.1 부팅·시작·리셋, 로고 밖/게임 화면 픽셀 비교, 실제 적용 도구를 검증했습니다.
에이전트의 전체 완주·실기·다른 에뮬레이터·오디오 청취 검수는 미수행입니다.
title.png는 배포 ROM과 같은 SHA-256의 실제 실행 캡처를 그대로 보존한 이미지입니다.

원본 ROM·BIOS·패치 완료 ROM은 포함하지 않습니다.
프로젝트: https://github.com/akuma815/nes-ninja-kun-majou-no-bouken-kr-patch
릴리즈: https://github.com/akuma815/nes-ninja-kun-majou-no-bouken-kr-patch/releases/tag/v1.0
