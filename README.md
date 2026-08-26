# NEON BEAT

E드라이브에 만들다 만 9키 리듬게임을 살린 로컬 음악게임입니다.
클론하면 `musik/` 안의 4곡으로 바로 플레이됩니다.

## 실행

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1
```

브라우저가 http://127.0.0.1:8766 를 엽니다.

## 조작

- 키: W A S D SPACE J K L I
- 마우스로 레인을 눌러도 판정됩니다
- ESC: 일시정지

## 곡

`musik/` 폴더:

- Okay Okay.wav
- Playlist_20+.wav
- 마지막 정류장.wav
- 빙글빙글.wav

커버와 타이틀 배경은 `assets/` 에 있습니다.

## 파일

- `index.html` 게임
- `server.py` 로컬 서버
- `musik/` 음원
- `assets/` 커버/배경 이미지
