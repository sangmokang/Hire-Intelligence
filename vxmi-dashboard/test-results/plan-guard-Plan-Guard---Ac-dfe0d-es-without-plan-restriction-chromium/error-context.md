# Page snapshot

```yaml
- generic [ref=e2]:
  - generic [ref=e5]:
    - generic [ref=e6]:
      - img "Value Connect" [ref=e7]
      - heading "로그인" [level=1] [ref=e8]
      - paragraph [ref=e9]: Value Connect에 오신 것을 환영합니다
    - button "Google로 계속하기" [ref=e10]:
      - img [ref=e11]
      - generic [ref=e16]: Google로 계속하기
    - generic [ref=e19]: 또는
    - generic [ref=e21]: Invalid API key
    - generic [ref=e22]:
      - textbox "이메일 주소" [ref=e24]: admin@valueconnect.kr
      - textbox "비밀번호" [ref=e26]: admin1234
      - generic [ref=e27]:
        - generic [ref=e28] [cursor=pointer]:
          - checkbox "로그인 상태 유지" [ref=e29]
          - generic [ref=e30]: 로그인 상태 유지
        - link "비밀번호 찾기" [ref=e31] [cursor=pointer]:
          - /url: /forgot-password
      - button "이메일로 로그인" [ref=e32]
    - paragraph [ref=e33]:
      - text: 계정이 없으신가요?
      - link "회원가입" [ref=e34] [cursor=pointer]:
        - /url: /register
  - generic [ref=e35]:
    - img [ref=e37]
    - button "Open Tanstack query devtools" [ref=e85] [cursor=pointer]:
      - img [ref=e86]
```