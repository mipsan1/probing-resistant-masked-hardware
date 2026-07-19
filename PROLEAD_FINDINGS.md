# PROLEAD 실측 결과 — 중대 발견 (2026-07-19)

## 실행 환경
- PROLEAD 네이티브 빌드(`PROLEAD/release/PROLEAD`, macOS arm64), 1,536,000 시뮬레이션, 1차 프로빙, transitional_leakage=true
- 리포의 PROLEAD 통합은 한 번도 실행된 적 없는 스캐폴이었음(config·CLI·라이브러리 alias·넷리스트 형식 전부 실측으로 교정)

## 최종 판정 (sim/*/prolead_circuit_0_0_1536000_leakages.json)

| 회로 | probing sets | leaking | 최악 -log10(p) | 판정 |
|---|---|---|---|---|
| 마스크드(d=1) | 2816 | **160** | **inf** (p=0) | **LEAKAGE** |
| 언마스크드(대조) | 1155 | 608 | inf | LEAKAGE (예상대로) |

- 대조 회로가 강하게 플래그됨 → 탐지 파이프라인 정상.
- 마스크드 회로: 시뮬 수 증가에 따라 10.2 → 25.6 → 118.3 → 198.6 → 최종 inf. 누설 와이어 3개(_000319_, _000503_, _000506_, 사이클 3·5)를 속성 보존 넷리스트로 역추적한 결과 **전부 mul1 단계 레지스터의 D 입력**(rtl/masked_sbox_first_order.v:235-245).

## 근본 원인 — RTL이 논문 Algorithm 1의 레지스터 배리어를 구현하지 않음

논문 Algorithm 1 (manuscript.tex:229): `q_ij ← Reg(p_ij ⊕ r_ij)` — **모든 갱신된 크로스 텀을 압축 전에 개별 레지스터에 저장**. Lemma(글리치 강건 비완전성, :292)도 "products with different indices are never merged before being registered"에 의존.

RTL (masked_sbox_first_order.v:240-243):
```
mul1_0 <= (gf_mul(x0_s1,x0_s2) ^ r0 ^ r1) ^ (gf_mul(x1_s1,x0_s2) ^ r2 ^ r3);
```
→ 크로스 텀을 **조합 논리로 먼저 XOR한 뒤** 레지스터에 저장. 글리치 확장 프로브 1개가 이 콘을 찌륵면 콘 입력 {x0_s1, x1_s1, x0_s2, r0..r3} 전부가 보이고, x0_s1 ⊕ x1_s1 = x² (시크릿)이 즉시 노출. 7개 곱셈 단계 전부 동일 구조.

즉: 표준 probing 모델에서는 1차 안전이 수학적으로 성립하지만, **논문이 채택한 robust(glitch-extended) 모델에서는 1차 안전이 성립하지 않는다**. PROLEAD 판정이 정확하며, 논문의 핵심 주장(robust d-probing 안전, 증명됨)과 구현이 모순된다.

## 수정 옵션 (인터페이스 영향)

- (A) Algorithm 1 그대로: 곱셈당 마스크 1바이트(r01), q00=Reg(p00), q01=Reg(p01^r01), q10=Reg(p10^r01), q11=Reg(p11). randomIn 224→56비트. 포트·테스트벤치 전부 변경.
- (B) 4마스크 인터페이스 유지 변형: q00=Reg(p00^r0^r3), q01=Reg(p01^r1), q10=Reg(p10^r2), q11=Reg(p11^r0^r1^r2^r3). 모든 2-집합이 마스크됨을 수기 검증. 포트 목록 불변, 논문의 R(d)=C(d+1,2) 기술과는 불일치.
- (C) 주의: 같은 마스크를 같은 출력 도메인의 두 텀에 재사용(q00,q10에 r01)하면 q00^q10 = A·b0가 노출되어 여전히 누설 — 수기 검증으로 기각.

공통: 곱셈당 레지스터 1단계 추가 → 파이프라인 지연 증가(10→~17사이클), config의 clock_cycles 조정, 전력/TVLA 등 하류 실험 전부 재측정 필요. d=2 설계(masked_sbox_second_order.v)도 같은 결함 가능성 검토 필요.

## 산출물
- sim/prolead/, sim/prolead_unmasked/ — leakages JSON
- sim/masked_prolead_stdout.log, sim/unmasked_prolead_stdout.log — 전체 stdout
- syn/prolead/run_full.py — 재현 러너(Automation automation_915e7c29)
- syn/prolead/circuit_struct_attr.v — src 속성 보존 넷리스트(와이어→RTL 역추적용)
